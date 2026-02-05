from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO
import json
import requests
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import whisper
import tempfile 
import ollama


model = whisper.load_model("base")


app = Flask(__name__)


# ==========================================
# LOCAL AI HELPER (OLLAMA)
# ==========================================
def ask_local_ai(prompt):

    res = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return res.json()["response"]


# ==========================================
# HOME
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# ANALYZE (LOCAL AI)
# ==========================================
@app.route("/analyze", methods=["POST"])
def analyze():

    print("ANALYZE API HIT (LOCAL AI) ✅")

    data = request.get_json() or {}

    meeting_text = data.get("meeting_text", "").strip()
    meeting_title = data.get("meeting_title", "Untitled Meeting")

    if not meeting_text:
        return jsonify({"error": "No meeting text provided"}), 400

    try:
        prompt = f"""
Return ONLY valid JSON. No explanation.

Format:
{{
  "summary": "",
  "key_points": [],
  "decisions": [],
  "action_items": [],
  "confidence": 90
}}

Meeting text:
{meeting_text}
"""

        ai_text = ask_local_ai(prompt)

        print("RAW AI:", ai_text)

        result = json.loads(ai_text)

    except Exception as e:
        print("LOCAL AI ERROR:", e)

        result = {
            "summary": "Could not analyze meeting.",
            "key_points": [],
            "decisions": [],
            "action_items": [],
            "confidence": 0
        }

    result["meeting_title"] = meeting_title

    return jsonify(result)

#       for voice upload    

@app.route("/transcribe", methods=["POST"])
def transcribe():

    file = request.files["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
        file.save(temp.name)

        result = model.transcribe(temp.name)

    return {"text": result["text"]}



# ==========================================
# EXPORT PDF
# ==========================================
@app.route("/export-pdf", methods=["POST"])
def export_pdf():

    print("PDF API HIT ✅")

    try:
        data = request.get_json() or {}

        buffer = BytesIO()

        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        elements = []

        elements.append(Paragraph("Meeting Summary Report", styles["Heading1"]))
        elements.append(Spacer(1, 20))

        summary = data.get("summary", "No summary provided")

        elements.append(Paragraph(summary, styles["BodyText"]))

        doc.build(elements)

        buffer.seek(0)

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="meeting_report.pdf"
        )

    except Exception as e:
        print("PDF ERROR:", e)
        return jsonify({"error": str(e)}), 500
    
#       chat box    

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json

        question = data.get("question", "")
        notes = data.get("notes", "")

        prompt = f"""
You are an AI meeting assistant.
Answer ONLY using the meeting context.

Meeting:
{notes}

Question:
{question}
"""

        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response["message"]["content"]

        return jsonify({"answer": answer})

    except Exception as e:
        print("CHAT ERROR:", e)   # 🔥 important
        return jsonify({"answer": "Server error. Check Flask console."})


# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)

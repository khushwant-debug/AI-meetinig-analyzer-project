"""
AI Meeting Analyzer - Model Logic
=================================
This file contains all the AI/ML logic extracted from the original Flask app.
Keep this separate from the UI to maintain clean separation of concerns.
"""

import json
import requests
import tempfile
from io import BytesIO

# Ollama API configuration
MODEL_API_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3"

# Try to import optional dependencies
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Global whisper model (lazy loaded)
_whisper_model = None


def get_whisper_model():
    """Load and return Whisper model (lazy loading)."""
    global _whisper_model
    if not WHISPER_AVAILABLE:
        raise ImportError("Whisper is not installed. Install with: pip install openai-whisper")
    
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    
    return _whisper_model


# ==========================================
# CORE AI FUNCTIONS
# ==========================================

def ask_local_ai(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Send a prompt to the local Ollama API and get the response.
    
    Args:
        prompt: The prompt to send to the AI
        model: The model to use (default: llama3)
    
    Returns:
        The AI's response as a string
    """
    try:
        res = requests.post(
            f"{MODEL_API_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120  # Add timeout for long-running requests
        )
        
        if res.status_code == 200:
            return res.json()["response"]
        else:
            raise Exception(f"Ollama API error: {res.status_code} - {res.text}")
            
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to Ollama at {MODEL_API_URL}. "
            "Please ensure Ollama is running. "
            "Start with: ollama serve"
        )


def analyze_meeting(meeting_text: str, meeting_title: str = "Untitled Meeting") -> dict:
    """
    Analyze meeting text and extract summary, key points, decisions, action items.
    
    Args:
        meeting_text: The raw meeting notes/transcript
        meeting_title: Optional title for the meeting
    
    Returns:
        Dictionary with analysis results:
        - summary: AI-generated summary
        - key_points: List of key points
        - decisions: List of decisions made
        - action_items: List of action items with assignees
        - confidence: Confidence score (0-100)
        - meeting_title: The meeting title
    """
    if not meeting_text or not meeting_text.strip():
        raise ValueError("Meeting text cannot be empty")
    
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
    
    try:
        ai_text = ask_local_ai(prompt)
        
        # Parse the JSON response
        result = json.loads(ai_text)
        
        # Validate and provide defaults for missing fields
        result = {
            "summary": result.get("summary", "No summary generated"),
            "key_points": result.get("key_points", []),
            "decisions": result.get("decisions", []),
            "action_items": result.get("action_items", []),
            "confidence": result.get("confidence", 50),
            "meeting_title": meeting_title
        }
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        raise Exception(f"Analysis failed: {str(e)}")


def chat_about_meeting(question: str, meeting_notes: str) -> str:
    """
    Answer questions about a meeting using the meeting context.
    
    Args:
        question: The user's question
        meeting_notes: The meeting notes to use as context
    
    Returns:
        The AI's answer
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    if not meeting_notes or not meeting_notes.strip():
        raise ValueError("Meeting notes cannot be empty")
    
    prompt = f"""
You are an AI meeting assistant.
Answer ONLY using the meeting context provided.
Be concise and helpful.

Meeting:
{meeting_notes}

Question:
{question}
"""
    
    try:
        # Try using the ollama library first
        try:
            import ollama
            response = ollama.chat(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except ImportError:
            # Fall back to API call
            return ask_local_ai(prompt)
            
    except Exception as e:
        raise Exception(f"Chat failed: {str(e)}")


def transcribe_audio(audio_file) -> str:
    """
    Transcribe an audio file using Whisper.
    
    Args:
        audio_file: File-like object or path to audio file
    
    Returns:
        The transcribed text
    """
    if not WHISPER_AVAILABLE:
        raise ImportError(
            "Whisper is not available. "
            "Install with: pip install openai-whisper"
        )
    
    # Save uploaded file to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
        audio_file.save(temp.name)
        temp_path = temp.name
    
    try:
        model = get_whisper_model()
        result = model.transcribe(temp_path)
        return result["text"]
    finally:
        # Clean up temp file
        import os
        try:
            os.unlink(temp_path)
        except:
            pass


def export_to_pdf(analysis_result: dict) -> BytesIO:
    """
    Export meeting analysis to PDF.
    
    Args:
        analysis_result: Dictionary with analysis results
    
    Returns:
        BytesIO buffer containing the PDF
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError(
            "ReportLab is not available. "
            "Install with: pip install reportlab"
        )
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    
    elements = []
    
    # Title
    meeting_title = analysis_result.get("meeting_title", "Meeting Summary")
    elements.append(Paragraph(meeting_title, styles["Heading1"]))
    elements.append(Spacer(1, 20))
    
    # Summary
    summary = analysis_result.get("summary", "No summary provided")
    elements.append(Paragraph("Summary", styles["Heading2"]))
    elements.append(Paragraph(summary, styles["BodyText"]))
    elements.append(Spacer(1, 15))
    
    # Key Points
    key_points = analysis_result.get("key_points", [])
    if key_points:
        elements.append(Paragraph("Key Points", styles["Heading2"]))
        for point in key_points:
            elements.append(Paragraph(f"• {point}", styles["BodyText"]))
        elements.append(Spacer(1, 15))
    
    # Decisions
    decisions = analysis_result.get("decisions", [])
    if decisions:
        elements.append(Paragraph("Decisions", styles["Heading2"]))
        for decision in decisions:
            elements.append(Paragraph(f"• {decision}", styles["BodyText"]))
        elements.append(Spacer(1, 15))
    
    # Action Items
    action_items = analysis_result.get("action_items", [])
    if action_items:
        elements.append(Paragraph("Action Items", styles["Heading2"]))
        for item in action_items:
            elements.append(Paragraph(f"• {item}", styles["BodyText"]))
        elements.append(Spacer(1, 15))
    
    # Confidence Score
    confidence = analysis_result.get("confidence", 0)
    elements.append(Paragraph(f"Confidence Score: {confidence}%", styles["Heading2"]))
    
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def check_ollama_connection() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get(f"{MODEL_API_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_available_models() -> list:
    """Get list of available Ollama models."""
    try:
        response = requests.get(f"{MODEL_API_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        return []
    except:
        return []

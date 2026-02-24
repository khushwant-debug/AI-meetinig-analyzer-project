"""
AI Meeting Analyzer - Model Logic
=================================
This file contains all the AI/ML logic for the Streamlit app.
Uses Groq API for cloud-based inference.

IMPORTANT: Set GROQ_API_KEY in Streamlit Cloud secrets or as environment variable.
"""

import os
import json
import re
import tempfile
from io import BytesIO

# Groq API configuration
# For Streamlit Cloud: Add GROQ_API_KEY in app settings (Secrets)
# For local: Set environment variable or create .env file

# Supported Groq model - using llama-3.1-8b-instant (fast, free, stable)
GROQ_MODEL = "llama-3.1-8b-instant"

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


def get_groq_client():
    """Initialize and return Groq client."""
    try:
        from groq import Groq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. "
                "For Streamlit Cloud: Add it in app settings (Secrets). "
                "For local: Set environment variable: export GROQ_API_KEY='your-key'"
            )
        return Groq(api_key=api_key)
    except ImportError:
        raise ImportError(
            "Groq SDK not installed. Install with: pip install groq"
        )


def get_whisper_model():
    """Load and return Whisper model (lazy loading)."""
    global _whisper_model
    if not WHISPER_AVAILABLE:
        raise ImportError(
            "Whisper is not installed. "
            "Install with: pip install openai-whisper"
        )
    
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    
    return _whisper_model


# ==========================================
# CORE AI FUNCTIONS
# ==========================================

def analyze_meeting(meeting_text: str, meeting_title: str = "Meeting Analysis") -> dict:
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
        - confidence: Confidence score
        - meeting_title: The meeting title
    """
    if not meeting_text or not meeting_text.strip():
        raise ValueError("Meeting text cannot be empty")
    
    prompt = f"""You are an AI meeting analyzer. Analyze the following meeting notes and return a structured JSON response.

Return ONLY valid JSON. No explanation before or after.

Required JSON format:
{{
  "summary": "A brief summary of the meeting (2-3 sentences)",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": ["Action item 1", "Action item 2"],
  "confidence": "A confidence score from 0-100%"
}}

Meeting notes:
{meeting_text}

JSON:"""

    try:
        client = get_groq_client()
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        ai_text = response.choices[0].message.content
        
        # Parse the JSON response
        result = json.loads(ai_text)
        
        # Validate and provide defaults for missing fields
        result = {
            "summary": result.get("summary", "No summary generated"),
            "key_points": result.get("key_points", []),
            "decisions": result.get("decisions", []),
            "action_items": result.get("action_items", []),
            "confidence": result.get("confidence", "50%"),
            "meeting_title": meeting_title
        }
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        error_msg = str(e)
        # Provide user-friendly error messages
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            raise Exception("API authentication failed. Please check your GROQ_API_KEY in Streamlit Secrets.")
        elif "rate limit" in error_msg.lower():
            raise Exception("Rate limit exceeded. Please wait a moment and try again.")
        elif "model" in error_msg.lower():
            raise Exception(f"Model error: {error_msg}. Please contact support.")
        else:
            raise Exception(f"Analysis failed: {error_msg}")


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
    
    prompt = f"""You are an AI meeting assistant. Answer the user's question based ONLY on the meeting context provided.

Meeting context:
{meeting_notes}

Question: {question}

Provide a clear, helpful answer based only on the meeting notes above."""

    try:
        client = get_groq_client()
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        # Provide user-friendly error messages
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            raise Exception("API authentication failed. Please check your GROQ_API_KEY in Streamlit Secrets.")
        elif "rate limit" in error_msg.lower():
            raise Exception("Rate limit exceeded. Please wait a moment and try again.")
        else:
            raise Exception(f"Chat failed: {error_msg}")


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
    confidence = analysis_result.get("confidence", "N/A")
    elements.append(Paragraph(f"Confidence Score: {confidence}", styles["Heading2"]))
    
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def check_groq_connection() -> bool:
    """Check if Groq API is accessible."""
    try:
        client = get_groq_client()
        # Try a simple API call to verify
        client.models.list()
        return True
    except Exception:
        return False

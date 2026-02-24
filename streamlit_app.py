"""
AI Meeting Analyzer - Streamlit App
===================================
A Streamlit-based interface for analyzing meeting notes.
Converted from Flask app for easy deployment on Streamlit Cloud.

Usage:
    streamlit run streamlit_app.py

Requirements:
    - Ollama running locally (for local AI)
    - Or configure for cloud API deployment
"""

import streamlit as st
import pandas as pd
from io import BytesIO

# Import our model logic
from model_logic import (
    analyze_meeting,
    chat_about_meeting,
    transcribe_audio,
    export_to_pdf,
    check_ollama_connection,
    WHISPER_AVAILABLE,
    REPORTLAB_AVAILABLE,
    MODEL_API_URL
)

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Meeting Analyzer",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .stButton > button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def display_analysis_results(result: dict):
    """Display the analysis results in a formatted way."""
    
    # Meeting Title
    meeting_title = result.get("meeting_title", "Meeting Analysis")
    st.markdown(f"## 📋 {meeting_title}")
    st.divider()
    
    # Summary
    st.subheader("📝 Summary")
    st.markdown(f">{result.get('summary', 'No summary available')}")
    
    # Create columns for layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Key Points
        key_points = result.get("key_points", [])
        if key_points:
            st.subheader("🔑 Key Points")
            for i, point in enumerate(key_points, 1):
                st.markdown(f"{i}. {point}")
    
    with col2:
        # Decisions
        decisions = result.get("decisions", [])
        if decisions:
            st.subheader("✅ Decisions")
            for i, decision in enumerate(decisions, 1):
                st.markdown(f"{i}. {decision}")
    
    # Action Items (full width)
    st.divider()
    action_items = result.get("action_items", [])
    if action_items:
        st.subheader("🎯 Action Items")
        for i, item in enumerate(action_items, 1):
            st.markdown(f"{i}. {item}")
    
    # Confidence Score
    confidence = result.get("confidence", 0)
    st.divider()
    st.subheader("📊 Confidence Score")
    
    # Display confidence as progress bar
    confidence_color = "green" if confidence >= 70 else "orange" if confidence >= 50 else "red"
    st.progress(confidence)
    st.markdown(f":{confidence_color}[**{confidence}%**]")
    
    # PDF Export
    if REPORTLAB_AVAILABLE:
        st.divider()
        try:
            pdf_buffer = export_to_pdf(result)
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_buffer,
                file_name="meeting_report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.warning(f"PDF export failed: {str(e)}")


def check_ollama_status():
    """Check and display Ollama connection status."""
    with st.sidebar:
        st.header("🔧 Configuration")
        
        if check_ollama_connection():
            st.success("✅ Ollama is connected")
        else:
            st.error(f"❌ Cannot connect to Ollama at {MODEL_API_URL}")
            st.info("""
            **To fix:**
            1. Make sure Ollama is installed
            2. Run `ollama serve` in terminal
            3. Pull model with: `ollama pull llama3`
            """)
        
        # Display optional dependencies status
        st.subheader("📦 Dependencies")
        st.write(f"- Whisper: {'✅ Available' if WHISPER_AVAILABLE else '❌ Not installed'}")
        st.write(f"- ReportLab: {'✅ Available' if REPORTLAB_AVAILABLE else '❌ Not installed'}")


# ==========================================
# MAIN APP
# ==========================================

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<p class="main-header">🤖 AI Meeting Analyzer</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Check Ollama status in sidebar
    check_ollama_status()
    
    # Initialize session state
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "meeting_text" not in st.session_state:
        st.session_state.meeting_text = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # ==========================================
    # INPUT SECTION
    # ==========================================
    
    st.header("📥 Input Meeting Notes")
    
    # Meeting title input
    meeting_title = st.text_input(
        "Meeting Title (optional)",
        placeholder="e.g., Weekly Team Standup",
        help="Give your meeting a descriptive title"
    )
    
    # Meeting notes textarea
    meeting_text = st.text_area(
        "Meeting Notes / Transcript",
        height=200,
        placeholder="Paste your meeting notes or transcript here...",
        help="Enter the raw meeting notes, transcript, or any text you want to analyze"
    )
    
    # ==========================================
    # AUDIO TRANSCRIPTION (Optional)
    # ==========================================
    
    st.subheader("🎤 Audio Transcription (Optional)")
    
    audio_option = st.radio(
        "Would you like to transcribe an audio file?",
        ["No", "Yes"],
        horizontal=True
    )
    
    if audio_option == "Yes":
        if WHISPER_AVAILABLE:
            audio_file = st.file_uploader(
                "Upload audio file",
                type=["mp3", "wav", "m4a", "ogg"],
                help="Supported formats: MP3, WAV, M4A, OGG"
            )
            
            if audio_file is not None:
                if st.button(" Transcription Audio", type="primary"):
                    with st.spinner("Transcribing audio..."):
                        try:
                            transcribed_text = transcribe_audio(audio_file)
                            meeting_text = meeting_text + "\n\n" + transcribed_text if meeting_text else transcribed_text
                            st.success("Audio transcribed successfully!")
                            st.text_area("Transcribed text (editable)", value=meeting_text, height=150, key="transcribed")
                        except Exception as e:
                            st.error(f"Transcription failed: {str(e)}")
        else:
            st.warning("Whisper is not installed. Install with: pip install openai-whisper")
    
    st.divider()
    
    # ==========================================
    # ANALYZE BUTTON
    # ==========================================
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        analyze_button = st.button(
            "🔍 Analyze Meeting",
            type="primary",
            disabled=not meeting_text.strip(),
            help="Click to analyze the meeting notes"
        )
    
    with col2:
        clear_button = st.button(
            "🗑️ Clear",
            help="Clear all inputs and results"
        )
    
    if clear_button:
        st.session_state.analysis_result = None
        st.session_state.chat_history = []
        st.rerun()
    
    # ==========================================
    # ANALYSIS EXECUTION
    # ==========================================
    
    if analyze_button and meeting_text.strip():
        try:
            with st.spinner("🤔 Analyzing meeting notes... This may take a moment."):
                result = analyze_meeting(meeting_text, meeting_title or "Meeting Analysis")
                st.session_state.analysis_result = result
                st.session_state.meeting_text = meeting_text
                
            st.success("✅ Analysis complete!")
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info("""
            **Troubleshooting:**
            - Make sure Ollama is running
            - Check the model is downloaded: `ollama pull llama3`
            - Verify the API URL is correct
            """)
    
    # ==========================================
    # RESULTS DISPLAY
    # ==========================================
    
    if st.session_state.analysis_result:
        st.divider()
        display_analysis_results(st.session_state.analysis_result)
        
        # ==========================================
        # CHAT SECTION
        # ==========================================
        
        st.divider()
        st.header("💬 Ask Questions About This Meeting")
        
        st.markdown("""
        <div class="success-box">
            💡 Tip: Ask questions like "What decisions were made?" or "Who is responsible for what?"
        </div>
        """, unsafe_allow_html=True)
        
        # Display chat history
        for i, (question, answer) in enumerate(st.session_state.chat_history):
            with st.expander(f"Q{i+1}: {question}", expanded=True):
                st.markdown(f"**You:** {question}")
                st.markdown(f"**AI:** {answer}")
        
        # Chat input
        st.subheader("Ask a follow-up question")
        
        if prompt := st.text_input(
            "Your question",
            placeholder="e.g., What are the next steps?",
            key="chat_input",
            label_visibility="collapsed"
        ):
            if st.button("Send", key="send_chat"):
                try:
                    with st.spinner("Getting answer..."):
                        answer = chat_about_meeting(
                            prompt,
                            st.session_state.meeting_text
                        )
                        st.session_state.chat_history.append((prompt, answer))
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Chat failed: {str(e)}")
    
    # ==========================================
    # FOOTER
    # ==========================================
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>AI Meeting Analyzer | Powered by Ollama (llama3)</p>
        <p>Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()

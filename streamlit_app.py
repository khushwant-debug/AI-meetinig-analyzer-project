"""
AI Meeting Analyzer - Streamlit App
===================================
A Streamlit-based interface for analyzing meeting notes.
Uses Groq API for cloud-based AI inference.

Usage:
    streamlit run streamlit_app.py

Requirements:
    - GROQ_API_KEY environment variable (for Streamlit Cloud, add in Secrets)
    - Set up: pip install groq
"""

import streamlit as st

# Import our model logic
from model_logic import (
    analyze_meeting,
    chat_about_meeting,
    check_groq_connection,
    get_groq_client
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
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def display_analysis_results(result: dict):
    """Display the analysis results in separate sections."""
    
    # Meeting Title
    meeting_title = result.get("meeting_title", "Meeting Analysis")
    st.markdown(f"## 📋 {meeting_title}")
    st.divider()
    
    # Summary
    st.subheader("📝 Summary")
    st.markdown(f">{result.get('summary', 'No summary available')}")
    
    st.divider()
    
    # Key Points
    st.subheader("🔑 Key Points")
    key_points = result.get("key_points", [])
    if key_points:
        for i, point in enumerate(key_points, 1):
            st.markdown(f"{i}. {point}")
    else:
        st.info("No key points identified")
    
    st.divider()
    
    # Decisions
    st.subheader("✅ Decisions")
    decisions = result.get("decisions", [])
    if decisions:
        for i, decision in enumerate(decisions, 1):
            st.markdown(f"{i}. {decision}")
    else:
        st.info("No decisions identified")
    
    st.divider()
    
    # Action Items
    st.subheader("🎯 Action Items")
    action_items = result.get("action_items", [])
    if action_items:
        for i, item in enumerate(action_items, 1):
            st.markdown(f"{i}. {item}")
    else:
        st.info("No action items identified")
    
    st.divider()
    
    # Confidence Score
    st.subheader("📊 Confidence Score")
    confidence = result.get("confidence", "N/A")
    
    # Try to parse confidence as number for progress bar
    try:
        confidence_numeric = int(confidence.strip('%').strip())
        confidence_color = "green" if confidence_numeric >= 70 else "orange" if confidence_numeric >= 50 else "red"
        st.progress(confidence_numeric)
        st.markdown(f":{confidence_color}[**{confidence}**]")
    except (ValueError, AttributeError):
        st.markdown(f"**{confidence}**")


def check_api_status():
    """Check and display API connection status."""
    with st.sidebar:
        st.header("🔧 Configuration")
        
        try:
            if check_groq_connection():
                st.success("✅ Groq API connected")
            else:
                st.error("❌ Cannot connect to Groq API")
        except ValueError as e:
            st.error(f"❌ API Key not configured")
            st.info("""
            **To fix:**
            1. For Streamlit Cloud: Add GROQ_API_KEY in app Secrets
            2. For local: Set environment variable:
               Windows: set GROQ_API_KEY=your-key
               Mac/Linux: export GROQ_API_KEY=your-key
            """)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


# ==========================================
# MAIN APP
# ==========================================

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<p class="main-header">🤖 AI Meeting Analyzer</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Check API status in sidebar
    check_api_status()
    
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
            
        except ValueError as e:
            st.error(f"❌ Configuration Error: {str(e)}")
            st.info("""
            **Fix: Add GROQ_API_KEY**
            - Local: Set environment variable
            - Streamlit Cloud: Add in app Secrets
            """)
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
    
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
                        
                except ValueError as e:
                    st.error(f"❌ Configuration Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Chat failed: {str(e)}")
    
    # ==========================================
    # FOOTER
    # ==========================================
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>AI Meeting Analyzer | Powered by Groq (LLama 3.3)</p>
        <p>Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()

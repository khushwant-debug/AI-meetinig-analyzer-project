# AI Meeting Analyzer - Deployment Guide

## 📁 Final Project Structure

```
AI Meeting Analyzer/
├── streamlit_app.py       # Main Streamlit application
├── model_logic.py         # AI logic (Groq API)
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit configuration
└── DEPLOYMENT.md          # This file
```

## 🚀 Local Development

### Prerequisites

1. **Python 3.8+** installed
2. **Groq API Key** - Get one at https://console.groq.com/

### Installation

```bash
# Clone or navigate to project
cd "AI Project"

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install optional dependencies (if needed)
pip install reportlab openai-whisper
```

### Running Locally

```
bash
# Set your API key (Windows)
set GROQ_API_KEY=your_api_key_here

# Set your API key (Mac/Linux)
export GROQ_API_KEY=your_api_key_here

# Run Streamlit app
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## ☁️ Streamlit Cloud Deployment

### Step 1: Prepare Your Code

The following files are needed:
- `streamlit_app.py`
- `model_logic.py`
- `requirements.txt`
- `.streamlit/config.toml`

### Step 2: Push to GitHub

```
bash
# Initialize git (if not already)
git init
git add .
git commit -m "Update to use Groq API"

# Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/ai-meeting-analyzer.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Streamlit Cloud

1. **Go to:** [share.streamlit.io](https://share.streamlit.io)

2. **Sign in** with your GitHub account

3. **Click "New app"**

4. **Configure deployment:**
   - Repository: `YOUR_USERNAME/ai-meeting-analyzer`
   - Branch: `main`
   - Main file path: `streamlit_app.py`

5. **Add API Key in Secrets:**
   
   In the Streamlit Cloud app settings, find "Secrets" and add:
   
   
```
   GROQ_API_KEY = "your_api_key_here"
   
```

6. **Click "Deploy"**

## ⚠️ Important Notes

### Groq API

- **Free Tier:** Groq offers free API access with generous limits
- **Model Used:** llama-3.1-70b-versatile (fast inference)
- **Rate Limits:** Check Groq console for current limits

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GROQ_API_KEY | Your Groq API key | Yes |

### Features Status

| Feature | Status | Notes |
|---------|--------|-------|
| Meeting Analysis | ✅ | Uses Groq Llama 3.1 |
| Chat Q&A | ✅ | Uses Groq Llama 3.1 |
| Audio Transcription | ⚠️ | Requires openai-whisper |
| PDF Export | ⚠️ | Requires reportlab |

## 🔧 Troubleshooting

### Common Issues

1. **"GROQ_API_KEY not found"**
   - Add GROQ_API_KEY in Streamlit Cloud Secrets
   - Or set as environment variable locally

2. **"Whisper not found"**
   - Install: `pip install openai-whisper`
   - Note: Requires more resources

3. **"ReportLab not found"**
   - Install: `pip install reportlab`

4. **API Errors**
   - Check Groq console for API status
   - Verify your API key is valid

## 📄 License

MIT License - Feel free to use and modify!

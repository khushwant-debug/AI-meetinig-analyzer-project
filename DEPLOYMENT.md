# AI Meeting Analyzer - Deployment Guide

## 📁 Project Structure

```
AI Meeting Analyzer/
├── streamlit_app.py       # Main Streamlit application
├── model_logic.py         # AI/ML logic (Ollama, Whisper, PDF)
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── DEPLOYMENT.md          # This file
└── README.md              # Project documentation
```

## 🚀 Local Development

### Prerequisites

1. **Python 3.8+** installed
2. **Ollama** installed and running locally

### Installation

```
bash
# Clone or navigate to project
cd "AI Project"

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install optional dependencies (if needed)
pip install openai-whisper reportlab ollama
```

### Running Locally

```
bash
# Start Ollama (in a separate terminal)
ollama serve
ollama pull llama3

# Run Streamlit app
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## ☁️ Streamlit Cloud Deployment

### Step 1: Prepare Your Code

1. **Keep essential files only:**
   - `streamlit_app.py`
   - `model_logic.py`
   - `requirements.txt`
   - `.streamlit/config.toml`

2. **Update requirements.txt for cloud:**
   
   For Streamlit Cloud, you'll need a cloud AI API instead of local Ollama. Update `requirements.txt`:
   
```
   streamlit>=1.28.0
   requests>=2.31.0
   openai>=1.0.0
   
```

3. **Update model_logic.py for cloud:**
   
   Replace Ollama calls with OpenAI API:
   
```
python
   # Change these in model_logic.py:
   
   # Instead of ask_local_ai(), use:
   from openai import OpenAI
   client = OpenAI(api_key="your-api-key")
   
   response = client.chat.completions.create(
       model="gpt-4",
       messages=[{"role": "user", "content": prompt}]
   )
   return response.choices[0].message.content
   
```

### Step 2: Push to GitHub

```
bash
# Initialize git (if not already)
git init
git add .
git commit -m "Convert to Streamlit app"

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

5. **Click "Deploy"**

### Step 4: Set Environment Variables (for Cloud AI)

In Streamlit Cloud dashboard:

1. Go to your app settings
2. Click "Secrets"
3. Add your API keys:
   
```
   OPENAI_API_KEY=sk-your-key-here
   
```

## ⚠️ Important Notes

### Local vs Cloud Deployment

| Feature | Local (Ollama) | Cloud (OpenAI) |
|---------|---------------|----------------|
| AI Model | llama3 (local) | GPT-4/GPT-3.5 |
| Cost | Free | Pay-per-use |
| Setup | Requires Ollama | Just API key |
| Speed | Depends on hardware | Fast (API) |

### For Full Local Experience

To keep using local AI with Streamlit Cloud:

1. Use **Streamlit Community Cloud** with a cloud service
2. Or host Ollama on a cloud server (AWS, GCP, etc.)
3. Update `MODEL_API_URL` in `model_logic.py` to point to your cloud Ollama instance

## 🔧 Troubleshooting

### Common Issues

1. **"Cannot connect to Ollama"**
   - Ensure Ollama is running: `ollama serve`
   - Check MODEL_API_URL in model_logic.py

2. **"Whisper not found"**
   - Install: `pip install openai-whisper`
   - Note: Whisper requires more resources

3. **"ReportLab not found"**
   - Install: `pip install reportlab`

4. **Streamlit Cloud errors**
   - Check app logs in Streamlit Cloud dashboard
   - Ensure all imports are in requirements.txt

## 📄 License

MIT License - Feel free to use and modify!

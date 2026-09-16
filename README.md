# ResumeIQ AI
RAG-powered ATS resume analyzer with a polished Streamlit frontend.

## Run
pip install -r requirements.txt
streamlit run app.py

## Streamlit Secrets
GEMINI_API_KEY = "your_key"
GEMINI_MODEL = "gemini-2.5-flash"

The app automatically falls back to local analysis if Gemini is unavailable.

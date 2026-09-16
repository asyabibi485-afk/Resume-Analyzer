# 📄 AI Resume Analyzer

A beginner-friendly RAG-powered resume analyzer for GitHub + Streamlit.

## Features
- PDF, DOCX and TXT resume upload
- Job description matching
- Skill matching and missing-skill detection
- ATS quality checks
- Role-specific analysis
- RAG knowledge base
- Gemini AI when `GEMINI_API_KEY` is available
- Local fallback analyzer when Gemini is unavailable

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Secrets

In Streamlit Cloud, add:

```toml
GEMINI_API_KEY = "your_api_key_here"
GEMINI_MODEL = "gemini-2.5-flash"
```

If Gemini fails or the key is missing, the app automatically uses the local analyzer instead of crashing.

## GitHub deployment

1. Create a GitHub repository.
2. Upload all files and folders from this project.
3. On Streamlit Cloud, create a new app.
4. Select the repository and branch.
5. Set the main file to `app.py`.
6. Add the secrets shown above.
7. Deploy.

## RAG

The `data/` folder contains small text knowledge bases. `rag.py` retrieves relevant guidance based on the target role and job description.

For a larger production RAG system, you can later add embeddings and a vector database.

## Gradio

The project is structured so the analysis functions in `backend.py` can be connected to a Gradio interface later. Streamlit is the current deployment entry point.

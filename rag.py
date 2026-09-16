import os
import re
from pathlib import Path

KB_DIR = Path(__file__).parent / "data"

def load_documents():
    docs = []
    if not KB_DIR.exists():
        return docs
    for path in KB_DIR.glob("*.txt"):
        try:
            docs.append((path.name, path.read_text(encoding="utf-8")))
        except Exception:
            pass
    return docs

def retrieve_guidance(role: str, job_description: str, top_k: int = 3):
    query = set(re.findall(r"[a-zA-Z]{3,}", f"{role} {job_description}".lower()))
    scored = []
    for name, text in load_documents():
        words = set(re.findall(r"[a-zA-Z]{3,}", text.lower()))
        score = len(query & words)
        scored.append((score, name, text))
    scored.sort(reverse=True)
    results = []
    for score, _, text in scored[:top_k]:
        if score > 0:
            for chunk in re.split(r"\n\s*\n", text):
                if chunk.strip():
                    results.append(chunk.strip())
    return results[:top_k]

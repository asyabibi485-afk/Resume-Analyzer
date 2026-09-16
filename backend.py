import os
import re
import json
from typing import List, Dict

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from docx import Document
except Exception:
    Document = None

from rag import retrieve_guidance

COMMON_SKILLS = {
    "python", "excel", "microsoft excel", "word", "powerpoint", "sql",
    "data entry", "data analysis", "data validation", "documentation",
    "communication", "customer service", "administration", "administrative",
    "computer operator", "computer operations", "reporting", "research",
    "project management", "leadership", "teamwork", "problem solving",
    "time management", "database", "data management", "machine learning",
    "artificial intelligence", "rag", "streamlit", "gradio", "github",
    "html", "css", "javascript", "python", "bioinformatics", "medical transcription"
}

def extract_text_from_file(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        if PdfReader is None:
            raise RuntimeError("PDF support is unavailable. Install pypdf.")
        import io
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    if name.endswith(".docx"):
        if Document is None:
            raise RuntimeError("DOCX support is unavailable. Install python-docx.")
        import io
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError("Unsupported file type.")

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def extract_skills(text: str) -> List[str]:
    t = normalize(text)
    found = []
    for skill in COMMON_SKILLS:
        if skill in t:
            found.append(skill)
    return sorted(set(found))

def extract_keywords(job_description: str) -> List[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", job_description.lower())
    stop = {
        "the","and","for","with","from","that","this","are","you","your","our",
        "will","have","has","job","role","work","required","requirements",
        "candidate","years","year","into","about","their","they","who"
    }
    counts = {}
    for w in words:
        if w not in stop:
            counts[w] = counts.get(w, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:20]]

def ats_checks(resume: str) -> List[Dict]:
    t = normalize(resume)
    checks = [
        ("Contact information", bool(re.search(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", t) or re.search(r"\+?\d[\d\s().-]{7,}", t)),
        ("Professional summary/profile", any(x in t for x in ["summary", "profile", "objective"])),
        ("Work experience", any(x in t for x in ["experience", "employment", "work history"])),
        ("Education", "education" in t),
        ("Skills section", "skills" in t),
        ("Action/achievement language", any(x in t for x in ["managed", "developed", "created", "improved", "increased", "reduced", "implemented", "analyzed"])),
        ("Quantifiable achievements", bool(re.search(r"\b\d+%|\b\d+\+|\$\d+|\b\d+\s+(?:years|months|clients|projects|records)\b", t))),
        ("Readable length", 150 <= len(t.split()) <= 1400),
    ]
    return [{"name": n, "passed": p, "details": "Pass" if p else "Needs improvement"} for n, p in checks]

def local_analysis(resume: str, job_description: str, role: str) -> Dict:
    resume_skills = set(extract_skills(resume))
    job_skills = set(extract_skills(job_description))
    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    if job_skills:
        match = round(len(matched) / len(job_skills) * 100)
    else:
        job_words = set(extract_keywords(job_description))
        resume_words = set(extract_keywords(resume))
        match = round(len(job_words & resume_words) / max(1, len(job_words)) * 100)

    checks = ats_checks(resume)
    ats = round(sum(x["passed"] for x in checks) / len(checks) * 100)

    guidance = retrieve_guidance(role, job_description)
    recommendations = []
    if missing:
        recommendations.append("Add relevant missing skills only if you genuinely have them.")
        recommendations.append("Reflect important job-description keywords naturally in your experience and skills sections.")
    if not any(x["name"] == "Quantifiable achievements" and x["passed"] for x in checks):
        recommendations.append("Add measurable achievements such as records processed, time saved, accuracy, volume, or percentages where truthful.")
    if not any(x["name"] == "Action/achievement language" and x["passed"] for x in checks):
        recommendations.append("Rewrite duties with action verbs and specific outcomes.")
    recommendations.extend(guidance[:3])
    if not recommendations:
        recommendations.append("Keep the resume tailored to the target role and verify every claim is accurate.")

    overall = round((match * 0.6) + (ats * 0.4))
    summary = f"The resume has a {match}% keyword/skill match with the supplied job description and an ATS-quality score of {ats}%. Target role: {role or 'Not specified'}."

    return {
        "job_match_score": match,
        "ats_score": ats,
        "overall_score": overall,
        "role_summary": summary,
        "matched_skills": matched,
        "missing_skills": missing,
        "ats_checks": checks,
        "recommendations": list(dict.fromkeys(recommendations)),
        "keywords": extract_keywords(job_description),
        "improved_summary": "Tailor the professional summary to the target role, emphasizing the strongest matching skills, relevant experience, and measurable results. Do not add skills or experience you do not have."
    }

def gemini_analysis(resume: str, job_description: str, role: str, api_key: str):
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = f"""You are an ATS resume analyst. Analyze the resume against the job description.
Return ONLY valid JSON with keys:
job_match_score (integer 0-100), ats_score (integer 0-100), overall_score (integer 0-100),
role_summary (string), matched_skills (array), missing_skills (array),
ats_checks (array of objects with name, passed, details),
recommendations (array), keywords (array), improved_summary (string).
Never invent candidate experience or skills.

TARGET ROLE:
{role}

RESUME:
{resume[:18000]}

JOB DESCRIPTION:
{job_description[:12000]}
"""
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
        )
        text = getattr(response, "text", "") or ""
        text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.I)
        result = json.loads(text)
        return result
    except Exception:
        return None

def analyze_resume(resume: str, job_description: str, role: str = "") -> Dict:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        result = gemini_analysis(resume, job_description, role, api_key)
        if result:
            return result
    return local_analysis(resume, job_description, role)

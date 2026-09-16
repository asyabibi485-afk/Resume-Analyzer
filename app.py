import streamlit as st
from backend import analyze_resume, extract_text_from_file

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")

st.title("📄 AI Resume Analyzer")
st.caption("RAG-powered resume, ATS, skills, and job-description matching")

with st.sidebar:
    st.header("Settings")
    role = st.text_input("Target Job Role", placeholder="e.g. Data Entry Operator")
    st.info("Upload a resume and paste the job description. Gemini is used when GEMINI_API_KEY is configured; otherwise the app uses a deterministic local analyzer.")

resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
job_description = st.text_area("Paste Job Description", height=260)

if st.button("🔎 Analyze Resume", type="primary", use_container_width=True):
    if not resume_file:
        st.error("Please upload a PDF, DOCX, or TXT resume.")
    elif not job_description.strip():
        st.error("Please paste the job description.")
    else:
        with st.spinner("Analyzing resume..."):
            try:
                resume_text = extract_text_from_file(resume_file)
                if not resume_text.strip():
                    st.error("Could not extract text from the resume.")
                else:
                    result = analyze_resume(resume_text, job_description, role.strip())
                    st.success("Analysis completed.")

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Job Match", f"{result['job_match_score']}%")
                    c2.metric("ATS Quality", f"{result['ats_score']}%")
                    c3.metric("Overall", f"{result['overall_score']}%")

                    st.subheader("🎯 Role Analysis")
                    st.write(result["role_summary"])

                    st.subheader("✅ Matched Skills")
                    st.write(", ".join(result["matched_skills"]) or "No clear matches found.")

                    st.subheader("⚠️ Missing / Weak Skills")
                    st.write(", ".join(result["missing_skills"]) or "No major missing skills detected.")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("ATS Checks")
                        for item in result["ats_checks"]:
                            st.write(("✅ " if item["passed"] else "⚠️ ") + item["name"] + ": " + item["details"])

                    with col2:
                        st.subheader("📌 Recommendations")
                        for rec in result["recommendations"]:
                            st.write("• " + rec)

                    st.subheader("🔑 Important Job Keywords")
                    st.write(", ".join(result["keywords"]) or "No keywords detected.")

                    st.subheader("📝 Suggested Resume Improvements")
                    st.write(result["improved_summary"])

                    with st.expander("View extracted resume text"):
                        st.text(resume_text)
            except Exception as e:
                st.error(f"Analysis error: {e}")

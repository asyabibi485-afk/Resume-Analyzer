import streamlit as st
from backend import analyze_resume, extract_text_from_file

st.set_page_config(page_title="ResumeIQ AI", page_icon="📄", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.block-container {padding: 2rem 4rem 3rem; max-width: 1400px;}
.hero {padding: 28px 32px; border-radius: 24px; background: linear-gradient(135deg,#111827 0%,#1e3a5f 55%,#2563eb 100%); color:white; margin-bottom:24px; box-shadow:0 12px 35px rgba(15,23,42,.18);}
.hero h1 {font-size:42px; margin:0 0 8px; font-weight:800; letter-spacing:-1px;}
.hero p {font-size:17px; margin:0; color:#dbeafe;}
.badge {display:inline-block; background:rgba(255,255,255,.13); border:1px solid rgba(255,255,255,.2); padding:6px 12px; border-radius:999px; font-size:13px; margin-bottom:12px;}
.section-title {font-size:24px; font-weight:750; color:#111827; margin:18px 0 10px;}
.card {background:#fff; border:1px solid #e5e7eb; border-radius:18px; padding:20px; box-shadow:0 5px 18px rgba(15,23,42,.06); height:100%;}
.metric {background:#fff; border:1px solid #e5e7eb; border-radius:18px; padding:18px; text-align:center; box-shadow:0 5px 18px rgba(15,23,42,.05);}
.metric .label {font-size:13px;color:#64748b;font-weight:650;text-transform:uppercase;letter-spacing:.6px;}
.metric .value {font-size:34px;font-weight:800;color:#0f172a;margin-top:4px;}
.skill {display:inline-block; background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; padding:6px 10px; border-radius:999px; margin:3px; font-size:13px;}
.missing {display:inline-block; background:#fff7ed; color:#c2410c; border:1px solid #fed7aa; padding:6px 10px; border-radius:999px; margin:3px; font-size:13px;}
.small {color:#64748b;font-size:13px;}
div[data-testid="stFileUploaderDropzone"] {border:2px dashed #93c5fd; border-radius:16px; background:#f8fbff;}
.stButton > button {border-radius:12px; height:48px; font-weight:700;}
textarea, input {border-radius:12px !important;}
</style>
""", unsafe_allow_html=True)

st.markdown('''<div class="hero"><div class="badge">✦ RAG + ATS + AI Resume Intelligence</div><h1>ResumeIQ AI</h1><p>Analyze your resume against any job description, discover skill gaps, and improve ATS readiness in seconds.</p></div>''', unsafe_allow_html=True)

st.markdown('<div class="section-title">1. Add your application details</div>', unsafe_allow_html=True)
left, right = st.columns([1,1.35], gap="large")
with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    role = st.text_input("Target job role", placeholder="e.g. Medical Transcriptionist")
    resume_file = st.file_uploader("Upload your resume", type=["pdf","docx","txt"], help="PDF, DOCX or TXT")
    if resume_file:
        st.success(f"✓ {resume_file.name} uploaded")
    st.markdown('<p class="small">Your resume is analyzed for skills, keywords, structure and ATS quality.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    job_description = st.text_area("Job description", height=230, placeholder="Paste the complete job description here...")
    st.markdown('<p class="small">For better matching, paste the full requirements, responsibilities and qualifications.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
    if not resume_file:
        st.error("Please upload your resume first.")
    elif not job_description.strip():
        st.error("Please paste the job description first.")
    else:
        with st.spinner("Analyzing resume with ATS + RAG intelligence..."):
            try:
                resume_text = extract_text_from_file(resume_file)
                if not resume_text.strip():
                    st.error("No readable text was found in this resume.")
                else:
                    result = analyze_resume(resume_text, job_description, role.strip())
                    st.session_state["result"] = result
                    st.session_state["resume_text"] = resume_text
            except Exception as e:
                st.error(f"Analysis error: {e}")

if "result" in st.session_state:
    result = st.session_state["result"]
    st.markdown('<div class="section-title">2. Your analysis</div>', unsafe_allow_html=True)
    a,b,c = st.columns(3, gap="medium")
    for col, label, key in [(a,"Job Match","job_match_score"),(b,"ATS Quality","ats_score"),(c,"Overall","overall_score")]:
        with col:
            st.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{result.get(key,0)}%</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Match & Skills", "📊 ATS Check", "💡 Recommendations", "🧠 RAG Insights"])
    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Role analysis")
        st.write(result.get("role_summary", ""))
        st.subheader("Matching skills")
        skills = result.get("matched_skills", [])
        st.markdown("".join(f'<span class="skill">✓ {s}</span>' for s in skills) or '<span class="small">No clear matching skills found.</span>', unsafe_allow_html=True)
        st.subheader("Missing or weak skills")
        missing = result.get("missing_skills", [])
        st.markdown("".join(f'<span class="missing">⚠ {s}</span>' for s in missing) or '<span class="small">No major gaps detected.</span>', unsafe_allow_html=True)
        st.subheader("Important keywords")
        st.write(", ".join(result.get("keywords", [])) or "No keywords detected.")
        st.markdown('</div>', unsafe_allow_html=True)
    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for item in result.get("ats_checks", []):
            icon = "✅" if item.get("passed") else "⚠️"
            st.write(f"{icon} **{item.get('name','Check')}** — {item.get('details','')}")
        st.markdown('</div>', unsafe_allow_html=True)
    with tab3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for rec in result.get("recommendations", []):
            st.markdown(f"**→** {rec}")
        st.subheader("Suggested improvement")
        st.write(result.get("improved_summary", ""))
        st.markdown('</div>', unsafe_allow_html=True)
    with tab4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("RAG uses the project's ATS and job-role knowledge base to add relevant guidance to the analysis.")
        st.info("Tip: Only add a skill or qualification if you genuinely have it. Tailor wording without inventing experience.")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<br><p class="small" style="text-align:center">ResumeIQ AI • RAG-powered resume analysis • Built with Python + Streamlit + Gradio + Gemini</p>', unsafe_allow_html=True)

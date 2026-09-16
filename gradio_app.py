import gradio as gr
from backend import analyze_resume, extract_text_from_file

def analyze(resume_file, job_description, role):
    if not resume_file:
        return "Please upload a resume."
    try:
        with open(resume_file, "rb") as f:
            class Upload:
                def __init__(self, name, data):
                    self.name, self._data = name, data
                def read(self):
                    return self._data
            upload = Upload(resume_file, f.read())
        resume = extract_text_from_file(upload)
        result = analyze_resume(resume, job_description, role)
        return f"""Job Match: {result['job_match_score']}%
ATS Quality: {result['ats_score']}%
Overall: {result['overall_score']}%

Matched Skills:
{', '.join(result['matched_skills']) or 'None'}

Missing/Weak Skills:
{', '.join(result['missing_skills']) or 'None'}

Recommendations:
{chr(10).join('- ' + x for x in result['recommendations'])}

Summary:
{result['role_summary']}
"""

demo = gr.Interface(
    fn=analyze,
    inputs=[
        gr.File(label="Resume", file_types=[".pdf", ".docx", ".txt"], type="filepath"),
        gr.Textbox(label="Job Description", lines=12),
        gr.Textbox(label="Target Role", placeholder="Data Entry Operator"),
    ],
    outputs=gr.Textbox(label="Analysis Report", lines=25),
    title="📄 AI Resume Analyzer",
    description="RAG-powered ATS and job-description matching."
)

if __name__ == "__main__":
    demo.launch()

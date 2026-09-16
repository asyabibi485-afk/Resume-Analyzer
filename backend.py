import os, re, json
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

COMMON_SKILLS={"python","excel","microsoft excel","word","powerpoint","sql","data entry","data analysis","data validation","documentation","communication","customer service","administration","administrative","computer operator","computer operations","reporting","research","project management","leadership","teamwork","problem solving","time management","database","data management","machine learning","artificial intelligence","rag","streamlit","gradio","github","html","css","javascript","bioinformatics","medical transcription","medical terminology","typing","confidentiality"}

def extract_text_from_file(uploaded_file):
    name=uploaded_file.name.lower(); data=uploaded_file.read()
    if name.endswith('.txt'): return data.decode('utf-8',errors='ignore')
    import io
    if name.endswith('.pdf'):
        if PdfReader is None: raise RuntimeError('PDF support unavailable. Install pypdf.')
        return '\n'.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(data)).pages)
    if name.endswith('.docx'):
        if Document is None: raise RuntimeError('DOCX support unavailable. Install python-docx.')
        return '\n'.join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    raise ValueError('Unsupported file type.')

def normalize(t): return re.sub(r'\s+',' ',t.lower()).strip()
def extract_skills(t):
    t=normalize(t); return sorted({s for s in COMMON_SKILLS if s in t})
def extract_keywords(t):
    words=re.findall(r'[a-zA-Z][a-zA-Z0-9+#.-]{2,}',t.lower()); stop={'the','and','for','with','from','that','this','are','you','your','our','will','have','has','job','role','work','required','requirements','candidate','years','year','their','they','who'}; counts={}
    for w in words:
        if w not in stop: counts[w]=counts.get(w,0)+1
    return [w for w,_ in sorted(counts.items(),key=lambda x:(-x[1],x[0]))[:20]]

def ats_checks(resume):
    t=normalize(resume)
    checks=[
      ('Contact information',bool(re.search(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b',t) or re.search(r'\+?\d[\d\s().-]{7,}',t))),
      ('Professional summary/profile',any(x in t for x in ['summary','profile','objective'])),
      ('Work experience',any(x in t for x in ['experience','employment','work history'])),
      ('Education','education' in t),('Skills section','skills' in t),
      ('Action/achievement language',any(x in t for x in ['managed','developed','created','improved','increased','reduced','implemented','analyzed'])),
      ('Quantifiable achievements',bool(re.search(r'\b\d+%|\b\d+\+|\$\d+|\b\d+\s+(?:years|months|clients|projects|records)\b',t))),
      ('Readable length',150 <= len(t.split()) <= 1400)]
    return [{'name':n,'passed':p,'details':'Pass' if p else 'Needs improvement'} for n,p in checks]

def local_analysis(resume,jd,role):
    rs=set(extract_skills(resume)); js=set(extract_skills(jd)); matched=sorted(rs&js); missing=sorted(js-rs)
    if js: match=round(len(matched)/len(js)*100)
    else:
        jw=set(extract_keywords(jd)); rw=set(extract_keywords(resume)); match=round(len(jw&rw)/max(1,len(jw))*100)
    checks=ats_checks(resume); ats=round(sum(x['passed'] for x in checks)/len(checks)*100); guidance=retrieve_guidance(role,jd)
    rec=[]
    if missing: rec.append('Add relevant missing skills only if you genuinely have them.'); rec.append('Reflect important job-description keywords naturally in your experience and skills sections.')
    if not any(x['passed'] for x in checks if x['name']=='Quantifiable achievements'): rec.append('Add truthful measurable achievements where possible.')
    if not any(x['passed'] for x in checks if x['name']=='Action/achievement language'): rec.append('Rewrite duties with action verbs and specific outcomes.')
    rec.extend(guidance[:3])
    return {'job_match_score':match,'ats_score':ats,'overall_score':round(match*.6+ats*.4),'role_summary':f'The resume has a {match}% skill/keyword match with the supplied job description and an ATS-quality score of {ats}%. Target role: {role or "Not specified"}.','matched_skills':matched,'missing_skills':missing,'ats_checks':checks,'recommendations':list(dict.fromkeys(rec)),'keywords':extract_keywords(jd),'improved_summary':'Tailor the professional summary to the target role, emphasizing genuine matching skills, relevant experience, and measurable results.'}

def gemini_analysis(resume,jd,role,key):
    try:
        from google import genai
        client=genai.Client(api_key=key)
        prompt=f'''Return ONLY valid JSON with keys: job_match_score, ats_score, overall_score, role_summary, matched_skills, missing_skills, ats_checks, recommendations, keywords, improved_summary. Scores must be integers 0-100. Never invent experience.\nROLE: {role}\nRESUME:\n{resume[:18000]}\nJOB DESCRIPTION:\n{jd[:12000]}'''
        r=client.models.generate_content(model=os.getenv('GEMINI_MODEL','gemini-2.5-flash'),contents=prompt)
        text=re.sub(r'^```json\s*|\s*```$','',(getattr(r,'text','') or '').strip(),flags=re.I); return json.loads(text)
    except Exception: return None

def analyze_resume(resume,job_description,role=''):
    key=os.getenv('GEMINI_API_KEY','').strip()
    if key:
        result=gemini_analysis(resume,job_description,role,key)
        if result: return result
    return local_analysis(resume,job_description,role)

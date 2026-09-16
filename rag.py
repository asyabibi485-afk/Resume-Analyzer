import re
from pathlib import Path
KB_DIR=Path(__file__).parent/'data'
def load_documents():
    out=[]
    for p in KB_DIR.glob('*.txt'):
        try: out.append((p.name,p.read_text(encoding='utf-8')))
        except Exception: pass
    return out
def retrieve_guidance(role,job_description,top_k=3):
    q=set(re.findall(r'[a-zA-Z]{3,}',f'{role} {job_description}'.lower())); scored=[]
    for name,text in load_documents(): scored.append((len(q&set(re.findall(r'[a-zA-Z]{3,}',text.lower()))),text))
    scored.sort(reverse=True); results=[]
    for score,text in scored[:top_k]:
        if score: results.extend(x.strip() for x in re.split(r'\n\s*\n',text) if x.strip())
    return results[:top_k]

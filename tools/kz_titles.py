"""03 COPY-01: a page title names the chapter or topic of the page (a noun phrase), never its point.
Shared by tools/qc_plan.py (page-plan titles) and tools/check_kz_project.py (titles on the rendered pages)."""
import re

PUNCT = re.compile(r'[：:—–，,。；;？?！!]|\s-\s')
# words that turn a topic name into a claim, a judgement or a question (the point belongs in the takeaway or the conclusion band)
CLAIM = re.compile(r'显著|提升|改善|降低|优于|劣于|领先|支持|证实|证明|提示|表明|有望|确保|需要|应当|必须|建议|是否|如何|为何|为什么|怎么|关键在于')
MAX_BODY = 14  # CJK characters; Latin words and digits count by character too, which is conservative

def title_findings(title, kind='content'):
    """→ [(level, code, message)]; level 'error' or 'warn'. Hero pages (cover, ending) carry the deck or study name and
    are only checked for punctuation."""
    out = []
    t = (title or '').strip()
    if PUNCT.search(t): out.append(('error', 'TITLE', '页标题不用冒号、破折号或句读（03 COPY-01）：标题写章节或主题名，观点放观点句或结论带'))
    if kind in ('cover', 'ending'): return out
    if CLAIM.search(t): out.append(('warn', 'TITLE-CLAIM', f'页标题像结论或问句（“{CLAIM.search(t).group(0)}”）：标题只写这一页讲的是哪一部分'))
    if len(re.sub(r'\s', '', t)) > MAX_BODY: out.append(('warn', 'TITLE-LONG', f'页标题超过 {MAX_BODY} 字：写成章节或主题名，细节放正文'))
    return out

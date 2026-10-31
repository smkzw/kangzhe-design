#!/usr/bin/env python3
"""09 NOTES-04/05: speaker-note checks (PPTX speaker notes, ppt-master notes/total.md, HTML-PPT aside.notes).

    python3 "$KZ_DIR/tools/check_notes.py" <project>/notes/total.md [--plan page-plan.json] [--json]
    python3 "$KZ_DIR/tools/check_notes.py" deck.pptx [--plan page-plan.json]
    python3 "$KZ_DIR/tools/check_notes.py" index.html [--plan page-plan.json]

Errors (exit 1):
  NOTES-HERO      cover / TOC / section / ending notes longer than one sentence
  NOTES-FILLER    stage directions that only announce the slide ("接下来我们看", "下面是", "这一页", "可以看到" …)
Warnings:
  NOTES-JARGON    engineering or management jargon (闭环、抓手、对齐、颗粒度、链路、落地 …)
  NOTES-TRANSL    translationese patterns (对……进行、作为一个、被……所、在……方面 …)
  NOTES-SENTENCE  a sentence too long to say in one breath (over 60 characters, or over 40 with no pause)
  NOTES-LIGHT     chatty fillers that make a protocol meeting sound casual (咱们、搞、挺、哈、啦、嘛 …)
  NOTES-MISSING   a page without notes (one finding when the whole deck has none)
Page kinds come from the page-plan (by page order); without it, the first page counts as the cover and pages whose
heading says 目录 / 章节 / 结束 / 尾页 / 谢谢 count as hero pages. The rules themselves are in design_specs/09.
"""
from pathlib import Path
import argparse, html, json, re, sys, zipfile

HERO = ('cover', 'toc', 'section', 'ending')
FILLER = re.compile(r'接下来(我们)?(来|再)?(看|讲|介绍|进入|是)|下面(我们)?(来|再)?(看|讲|介绍|进入|是)|这一页|这页|本页|这张(幻灯片|图|表)?|'
                    r'我们(来|先)?看(一下|看)?|(大家)?可以看到|如图所示|如上所示|值得(注意|关注)的是|需要指出的是|综上所述|总的来说|总而言之|'
                    r'让我们|下一页|上一页|本节(将|主要)|本章(将|主要)|首先(我们)?来')
JARGON = re.compile(r'闭环|抓手|赋能|对齐|颗粒度|链路|落地|打通|拉通|沉淀|方法论|底层逻辑|痛点|心智|组合拳|输出物|模块化')
TRANSL = re.compile(r'对[^，。；]{1,14}进行(了)?|作为一(个|种|项)|被[^，。；]{1,10}所|在[^，。；]{1,10}(方面|层面)|使得|一个[^，。；]{1,10}的过程|的的')
LIGHT = re.compile(r'咱们|搞|挺|蛮|超级|哈|啦|嘛|呗|哦|吧[。！？]|对吧|是不是')
SENT = re.compile(r'[^。！？!?；;]+[。！？!?；;]?')

def sentences(text):
    return [s.strip() for s in SENT.findall(text.replace('\n', '')) if s.strip(' 。！？!?；;')]

def from_md(path):
    """notes/total.md: '# heading' sections separated by '---' (ppt-master executor-notes)."""
    out = []
    for part in re.split(r'\n-{3,}\n', Path(path).read_text(encoding='utf-8')):
        m = re.match(r'\s*#\s*(.+?)\n(.*)', part, re.S)
        if m: out.append((m.group(1).strip(), m.group(2).strip(), None))
    return out

def from_pptx(path):
    z = zipfile.ZipFile(path); names = set(z.namelist()); out = []
    slides = sorted((int(m.group(1)) for n in names if (m := re.match(r'ppt/slides/slide(\d+)\.xml$', n))))
    for i in slides:
        rel = f'ppt/slides/_rels/slide{i}.xml.rels'
        target = re.search(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"', z.read(rel).decode('utf-8')) if rel in names else None
        text = ''
        if target:
            x = z.read('ppt/notesSlides/' + target.group(1)).decode('utf-8')
            body = re.search(r'<p:sp>(?:(?!</p:sp>).)*?type="body".*?</p:sp>', x, re.S)
            paras = re.findall(r'<a:p>(.*?)</a:p>', body.group(0) if body else '', re.S)
            text = '\n'.join(html.unescape(''.join(re.findall(r'<a:t>([^<]*)</a:t>', p))) for p in paras).strip()
        title = re.findall(r'<a:t>([^<]*)</a:t>', z.read(f'ppt/slides/slide{i}.xml').decode('utf-8'))
        out.append((html.unescape(title[0]) if title else f'slide {i}', text, None))
    return out

def from_html(path):
    s = Path(path).read_text(encoding='utf-8'); out = []
    for i, sec in enumerate(re.findall(r'<section\b.*?</section>', s, re.S), 1):
        t = re.search(r'data-title="([^"]*)"', sec)
        n = re.search(r'<aside class="notes"[^>]*>(.*?)</aside>', sec, re.S)
        hero = re.search(r'data-chrome="hero"', sec.split('>', 1)[0])  # the deck says which slides are hero pages
        head = html.unescape(t.group(1)) if t else f'slide {i}'
        kind = (guess_kind(0 if i == 1 else i, head, 10 ** 6) if hero else 'content')
        out.append((head, html.unescape(re.sub(r'<[^>]+>', '', n.group(1))).strip() if n else '', 'section' if hero and kind == 'content' else kind))
    return out

def load(path):
    p = str(path).lower()
    return from_pptx(path) if p.endswith('.pptx') else from_html(path) if p.endswith(('.html', '.htm')) else from_md(path)

def guess_kind(i, heading, n):
    if i == 0: return 'cover'
    if re.search(r'目录|议程', heading): return 'toc'
    if re.search(r'结束|尾页|谢谢|致谢|Q&A', heading, re.I) or (i == n - 1 and re.search(r'结束|讨论', heading)): return 'ending'
    if re.search(r'章节|^第[一二三四五六七八九十\d]+部分', heading): return 'section'
    return 'content'

def check(notes, kinds=None):
    found = []
    def add(level, code, where, msg): found.append({'level': level, 'code': code, 'where': where, 'message': msg})
    if notes and not any(t for _, t, _ in notes):  # exported without notes (--no-notes): one finding, not one per page
        add('warn', 'NOTES-MISSING', 'deck', f'{len(notes)} 页都没有讲稿；正式交付按 09 写讲稿'); return found
    for i, (head, text, marked) in enumerate(notes):
        kind = (kinds[i] if kinds and i < len(kinds) else None) or marked or guess_kind(i, head, len(notes))
        where = f'{i + 1:02d} {head}'
        if not text: add('warn', 'NOTES-MISSING', where, '没有讲稿'); continue
        ss = sentences(text)
        if kind in HERO and len(ss) > 1: add('error', 'NOTES-HERO', where, f'{kind} 页讲稿 {len(ss)} 句，限一句')
        for rx, level, code, msg in ((FILLER, 'error', 'NOTES-FILLER', '只在报幕的套话，删掉直接讲内容'),
                                     (JARGON, 'warn', 'NOTES-JARGON', '工程或管理行话，换成临床试验里的说法'),
                                     (TRANSL, 'warn', 'NOTES-TRANSL', '翻译腔句式，改成中文的主谓直说'),
                                     (LIGHT, 'warn', 'NOTES-LIGHT', '口头语偏随意，方案讨论会用平实书面口语')):
            hits = sorted({m.group(0) for m in rx.finditer(text)})
            if hits: add(level, code, where, f'{msg}：{"、".join(hits)}')
        for s in ss:
            pauses = len(re.findall(r'[，、,：:]', s)); n = len(s)
            if n > 60 or (n > 40 and pauses == 0):
                add('warn', 'NOTES-SENTENCE', where, f'{n} 字一句、{pauses} 处停顿，拆成短句：{s[:30]}…')
    return found

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('notes', type=Path); ap.add_argument('--plan', type=Path); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    kinds = [p['kind'] for p in json.loads(a.plan.read_text(encoding='utf-8'))['pages']] if a.plan else None
    notes = load(a.notes); found = check(notes, kinds)
    errs = [f for f in found if f['level'] == 'error']
    if a.json: print(json.dumps({'pages': len(notes), 'findings': found}, ensure_ascii=False, indent=1))
    else:
        for f in found: print(f'{f["level"].upper():5} {f["code"]:14} {f["where"]}: {f["message"]}')
        print(f'{len(notes)} pages of notes, {len(errs)} error(s), {len(found) - len(errs)} warning(s)')
    return 1 if errs else 0

if __name__ == '__main__':
    sys.exit(main())

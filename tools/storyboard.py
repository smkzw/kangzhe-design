#!/usr/bin/env python3
"""分页故事板 (17 SB): the second stop before anything is generated — every page of the page-plan on one sheet, so the
user approves or changes the page list, the template / stage per page and the order once.

  python3 tools/storyboard.py html page-plan.json --out storyboard.html     # cards per page; 「确认」 → kz-storyboard.json
  python3 tools/storyboard.py text page-plan.json                           # the same as a Markdown table for the chat

Per page: number, kind, title, what carries it (regular template with a thumbnail of its example and the other
templates of its family to swap to; flagship template; three.js stage with its steps; demo form), density, takeaway,
and the qc_plan findings of that page. The user marks each page 通过 / 要改 with a note; the agent applies the notes to
the page-plan and only then starts the engines.
"""
from pathlib import Path
from html import escape
import argparse, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'examples/templates'))
TOK = json.loads((ROOT / 'tokens/tokens.json').read_text(encoding='utf-8'))
KIND = {'cover': '封面', 'toc': '目录', 'section': '章节', 'body': '正文', 'ending': '尾页'}

def _catalog():
    import kz_layouts as K
    return {p['name']: p for p in K.catalog()}

def _thumb(name, cache={}):
    """Inline SVG of the template's own example page (examples/templates), scaled to a card; None when there is none."""
    if name in cache: return cache[name]
    try:
        import kz_layouts as K
        from pages import PAGES
        hit = next((p for p in PAGES if p[0] == name), None)
        if not hit: cache[name] = None; return None
        d = json.loads((ROOT / 'examples/templates' / hit[1]).read_text(encoding='utf-8'))
        body = K.render(name, d, 'pptx')[0]['svg']
        cache[name] = f'<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(name)} 版式示意"><rect width="1280" height="720" fill="#FBF8F3"/>{body}</svg>'
    except Exception:  # a thumbnail is a convenience; the card still lists the template by name
        cache[name] = None
    return cache[name]

def carrier(pg, plan, cat):
    """What draws the page: (label, detail, thumbnail template or None, swap list)."""
    st, tpl, demo = pg.get('stage'), pg.get('template'), pg.get('demo')
    if st:
        c = TOK['flagship']['stages']['catalog'].get(st.get('component'), {})
        return ('three.js 舞台', f'{st.get("component")} · {" → ".join(c.get("steps", []))}', None, [])
    if demo:
        kind = demo.get('kind') if isinstance(demo, dict) else demo
        return ('演示舞台', f'{kind}', None, [])
    if tpl and tpl.startswith('flag-'):
        return ('旗舰版式', tpl, None, [])
    if tpl and tpl in cat:
        fam = cat[tpl]['family']; same = [n for n, p in cat.items() if p['family'] == fam and n != tpl]
        return ('模板', f'{tpl} · {cat[tpl]["title"]}', tpl, same)
    if pg.get('kind') in ('cover', 'toc', 'section', 'ending'):
        return ('hero 版式', pg.get('hero_layout_id') or '—', None, [])
    if pg.get('kind') in ('hero', 'flow_section'):   # site and stream first screens and chapter heads: no body template
        return ('首屏 / 章节头', tpl or pg.get('fold_stage') or '—', None, [])
    return ('未指定', '正文页缺 template / stage / demo', None, [])

def rows(plan):
    from qc_plan import validate
    cat = _catalog(); found = validate(plan); by = {}; ids = [p['id'] for p in plan['pages']]
    def page_of(w):   # qc_plan names the page by id, or by a schema path pages/<n>/…
        w = str(w or ''); m = re.match(r'pages/(\d+)', w)
        if m and int(m[1]) < len(ids): return ids[int(m[1])]
        head = re.split(r'[/:\s]', w)[0]
        return head if head in ids else ''
    for f in found: f['page'] = page_of(f.get('where')); by.setdefault(f['page'], []).append(f)
    out = []
    for i, pg in enumerate(plan['pages'], 1):
        lab, det, th, same = carrier(pg, plan, cat)
        tk = pg.get('takeaway'); tk = tk.get('text') if isinstance(tk, dict) else tk
        out.append({'n': i, 'id': pg['id'], 'kind': KIND.get(pg.get('kind'), pg.get('kind')), 'title': pg.get('title', ''), 'carrier': lab, 'detail': det,
                    'thumb': th, 'swap': same, 'density': (pg.get('density') or pg.get('body_profile') or '') if pg.get('kind') == 'body' else '', 'takeaway': tk or '',
                    'findings': [f'{f["level"]} {f["code"]}：{f.get("message", "")}' for f in by.get(pg['id'], [])]})
    return out, [f for f in found if not f['page']]

def text(plan):
    rs, deck = rows(plan)
    lines = [f'分页故事板 · {plan.get("track")} · {plan.get("route") or "regular"} · {len(rs)} 页', '',
             '| # | 页型 | 标题 | 载体 | 密度 | 检查 |', '|---|---|---|---|---|---|']
    for r in rs:
        lines.append(f'| {r["n"]} | {r["kind"]} | {r["title"]} | {r["carrier"]}：{r["detail"]} | {r["density"]} | {"；".join(r["findings"]) or "—"} |')
    if deck: lines += ['', '整份 deck：' + '；'.join(f'{f["level"]} {f["code"]}' for f in deck)]
    lines += ['', '请逐页回复“通过”或“第 N 页改为……”，确认后才开始生成。']
    return '\n'.join(lines)

CSS = """:root{--b:%(brand)s;--ink:%(ink)s;--mut:%(muted)s;--risk:%(risk)s}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 "PingFang SC","Microsoft YaHei",sans-serif;color:%(body)s;background:#FBF8F3}
.hdr{position:sticky;top:0;z-index:2;display:flex;gap:1rem;align-items:center;padding:.9rem 3.2vw;background:rgba(255,255,255,.88);backdrop-filter:blur(12px);border-bottom:1px solid #EEE6DA}
.hdr b{color:var(--ink)}.hdr .meta{margin-left:auto;color:var(--mut);font-size:.9rem}
main{padding:1.4rem 3.2vw 7rem;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.2rem}@media(max-width:960px){main{grid-template-columns:1fr}}
.pg{background:#fff;border:1px solid #EFE6D9;border-radius:16px;overflow:hidden;box-shadow:0 10px 30px rgba(120,80,30,.06);display:flex;flex-direction:column}
.th{aspect-ratio:16/9;background:#F6EFE5;display:flex;align-items:center;justify-content:center;color:var(--mut);font-size:.85rem;border-bottom:1px solid #F0E7DA}
.th svg{width:100%%;height:100%%;display:block}.tx{padding:.7rem .9rem;display:flex;flex-direction:column;gap:.35rem;flex:1}
.n{color:var(--b);font-weight:800}.k{color:var(--mut);font-size:.82rem}.t{color:var(--ink);font-weight:700}
.c{font-size:.85rem}.c i{font-style:normal;color:var(--b);font-weight:700;margin-right:.3rem}.tk{font-size:.85rem;color:var(--ink)}
.f{font-size:.8rem;color:var(--risk)}.sw{font-size:.8rem;color:var(--mut)}
.act{display:flex;gap:.4rem;align-items:center;margin-top:auto;padding-top:.4rem}.act button{font:inherit;font-size:.85rem;border:1.5px solid #E5D9C8;background:#fff;border-radius:999px;padding:.25rem .8rem;cursor:pointer}
.act button.on{background:var(--b);border-color:var(--b);color:#fff}.act input{flex:1;font:inherit;font-size:.85rem;padding:.3rem .6rem;border:1.5px solid #EEE4D6;border-radius:10px}
.bar{position:fixed;left:0;right:0;bottom:0;display:flex;gap:.8rem;align-items:center;padding:.9rem 3.2vw;background:rgba(255,255,255,.94);border-top:1px solid #EEE6DA}
.bar .sum{flex:1;color:var(--mut);font-size:.9rem}.btn{font:inherit;border:0;border-radius:999px;padding:.6rem 1.3rem;background:var(--b);color:#fff;font-weight:700;cursor:pointer}
pre{grid-column:1/-1;white-space:pre-wrap;background:#fff;border:1px dashed var(--b);border-radius:14px;padding:1rem}
""" % {'brand': TOK['colors']['brand'], 'ink': TOK['colors']['ink'], 'muted': TOK['colors']['muted'], 'risk': TOK['colors']['risk'], 'body': TOK['colors']['body']}

JS = """const st={};document.querySelectorAll('.pg').forEach(p=>{const id=p.dataset.id;st[id]={ok:true,note:''};
 p.querySelectorAll('.act button').forEach(b=>b.onclick=()=>{st[id].ok=b.dataset.v==='ok';p.querySelectorAll('.act button').forEach(x=>x.classList.toggle('on',x===b));sum();});
 p.querySelector('.act input').oninput=e=>{st[id].note=e.target.value;if(e.target.value&&st[id].ok){p.querySelector('[data-v=fix]').click();}sum();};});
function sum(){const v=Object.values(st),fix=v.filter(x=>!x.ok).length;document.getElementById('sum').textContent=`${v.length} 页 · 通过 ${v.length-fix} · 要改 ${fix}`;}
document.getElementById('ok').onclick=()=>{const r=JSON.stringify({version:1,pages:Object.entries(st).map(([id,x])=>({id,ok:x.ok,note:x.note}))},null,1);
 const p=document.getElementById('out');p.hidden=false;p.textContent=r;const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([r],{type:'application/json'}));a.download='kz-storyboard.json';a.click();p.scrollIntoView({behavior:'smooth'});};
sum();"""

def html(plan, title=''):
    rs, deck = rows(plan); cards = []
    for r in rs:
        th = _thumb(r['thumb']) if r['thumb'] else None
        cards.append(f'<article class="pg" data-id="{escape(r["id"])}"><div class="th">{th or escape(r["carrier"] + " · " + r["detail"])}</div><div class="tx">'
                     f'<div><span class="n">{r["n"]:02d}</span> <span class="k">{escape(r["kind"])}{" · " + escape(r["density"]) if r["density"] else ""}</span></div>'
                     f'<div class="t">{escape(r["title"])}</div><div class="c"><i>{escape(r["carrier"])}</i>{escape(r["detail"])}</div>'
                     + (f'<div class="tk">观点：{escape(r["takeaway"])}</div>' if r['takeaway'] else '')
                     + (f'<div class="sw">同族可换：{escape("、".join(r["swap"][:6]))}</div>' if r['swap'] else '')
                     + ''.join(f'<div class="{"f" if x.startswith("error") else "sw"}">{escape(x)}</div>' for x in r['findings'])
                     + '<div class="act"><button class="on" data-v="ok">通过</button><button data-v="fix">要改</button><input placeholder="改成什么（换模板、并页、删页…）"></div></div></article>')
    meta = f'{plan.get("track")} · {"旗舰" if plan.get("route") == "flagship" else "常规"} · {len(rs)} 页'
    deck_f = ''.join(f'<div class="{"f" if f["level"] == "error" else "sw"}">整份 deck：{escape(f["level"])} {escape(f["code"])} {escape(f.get("message", ""))}</div>' for f in deck)
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>康哲 Design · 分页故事板</title><style>{CSS}</style></head><body>'
            f'<header class="hdr"><b>康哲 Design · 分页故事板{(" · " + escape(title)) if title else ""}</b><div class="meta">第 2 站 / 共 2 站 · {escape(meta)} · 确认后开始生成</div></header>'
            f'<main>{deck_f and "<div style=grid-column:1/-1>" + deck_f + "</div>"}{"".join(cards)}<pre id="out" hidden></pre></main>'
            '<div class="bar"><div class="sum" id="sum"></div><button class="btn" id="ok">确认，开始生成 →</button></div>'
            f'<script>{JS}</script></body></html>')

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0]); sub = ap.add_subparsers(dest='cmd', required=True)
    h = sub.add_parser('html'); h.add_argument('plan'); h.add_argument('--out', required=True); h.add_argument('--title', default='')
    t = sub.add_parser('text'); t.add_argument('plan')
    o = ap.parse_args(argv); plan = json.loads(Path(o.plan).read_text(encoding='utf-8'))
    if o.cmd == 'html': Path(o.out).write_text(html(plan, o.title), encoding='utf-8'); print(o.out)
    else: print(text(plan))
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""开工卡 (17 INTAKE): every decision the work needs, asked once, then prefilled into the upstream engines so that
ppt-master / html-ppt-skill do not ask again.

  python3 tools/intake.py html  --out intake.html [--topic 主题] [--detected 生图能力] [--prefill pre.json]
        the picker page; 「确认」 downloads kz-intake.json and shows the same JSON to copy back into the chat
  python3 tools/intake.py ask   [--detected 生图能力] [--prefill pre.json]
        the same questions as AskUserQuestion batches (≤4 questions × ≤4 options) for hosts without a browser
  python3 tools/intake.py apply kz-intake.json
        validate the answers → page-plan fields, the context_pack command, the upstream prefill and the scenario-family
        products to use (template / demo form / flagship stage / flagship PPTX)

The question set is data (QUESTIONS); the background styles come from tokens.image.backdrop.styles.
"""
from pathlib import Path
from html import escape
import argparse, json, sys

ROOT = Path(__file__).resolve().parents[1]
TOK = json.loads((ROOT / 'tokens/tokens.json').read_text(encoding='utf-8'))
STYLES = TOK['image']['backdrop']['styles']

# scenario family → (label, static template, regular demo form, flagship stage, flagship PPTX template, description)
SCENES = {
    'safety': ('安全性总览', 'safety-overview', 'safety', 'safety', 'flag-safety', 'TEAE、TRAE、SAE、AESI 分层与组间差'),
    'program': ('临床开发计划', 'program-plan', 'program', 'program', 'flag-program', '多适应症泳道与关键里程碑'),
    'exposure': ('暴露例数', 'exposure-summary', 'exposure', 'exposure', 'flag-exposure', '各适应症按暴露时长档的例数与人年'),
    'trialflow': ('试验流程', 'trial-flow', 'trialflow', 'trialflow', 'flag-trialflow', '随机化、剂量递增、再随机化与随访'),
    'landscape': ('竞争格局', 'landscape', 'landscape', 'landscape', 'flag-landscape', '研发阶段、疗效与耐受性对比'),
    'efficacy': ('有效性汇总', 'efficacy-summary', 'efficacy', 'efficacy', 'flag-efficacy', '主要与次要终点、各组差值与 95% CI'),
    'soa': ('访视流程 SoA', 'soa', 'soa', 'soa', 'flag-soa', '入组、主要终点访视、给药与背景治疗期、每次访视的具体评估项目'),
    # round 9 (None: that product does not exist for the family — the HTML figure itself is interactive)
    'exposure_plan': ('累计暴露与 NDA', 'exposure-plan', None, None, 'flag-exposure-plan', '按开发计划累计暴露，各适应症 NDA 时对照 ICH E1；与甘特同一份数据'),
    'longitudinal': ('历时变化', 'longitudinal', None, None, None, '有效性与安全性指标按访视的变化（各组或盲态全体），检验箱线与小倍数'),
    'landscape_many': ('竞争格局（竞品多）', 'landscape-pipeline', None, None, None, '>8 个竞品：研发格局、有效性、安全性分三页'),
}

def questions(detected=None):
    det = detected or '未检测到'
    return [
        {'key': 'track', 'title': '交付形式', 'note': '决定制作引擎', 'default': 'pptx', 'options': [
            ('pptx', '可编辑 PPTX', 'PowerPoint 里能改字、改图表；正式汇报与留档（ppt-master）'),
            ('htmlppt', 'HTML-PPT', '浏览器全屏放映，分步演示与 three.js 舞台（html-ppt-skill）'),
            ('site', '站点式 HTML', '一屏总览 + 下钻，发链接自看'),
            ('stream', '流式 HTML', '长文阅读，左侧固定目录')]},
        {'key': 'route', 'title': '路线', 'note': '只对 PPTX 与 HTML-PPT，判据见 14 FLAG-01', 'default': 'regular', 'when': ('pptx', 'htmlppt'), 'options': [
            ('regular', '常规', '日常与内部汇报：同族玻璃卡、模板库正文'),
            ('flagship', '旗舰', '对外与顶层汇报：棱面页眉、白纸卡；HTML 用 three.js 舞台，PPTX 用层叠纸板')]},
        {'key': 'image', 'title': '生图能力', 'note': f'检测结果：{det}；见 04 IMG-07', 'default': 'generate' if detected else 'default_set', 'when': ('pptx', 'htmlppt'), 'options': [
            ('generate', '用检测到的能力生图', f'按主题生成封面与章节主视觉（{det}）'),
            ('other', '另指定生图方式', '在备注里写 skill、接口或服务名'),
            ('default_set', '不生图，用缺省背景套', '常规用 assets/backgrounds/，旗舰用 flagship-cover')]},
        {'key': 'background', 'title': '背景风格', 'note': '常规路线；旗舰固定暖白画布', 'default': STYLES['default'], 'when_route': 'regular', 'options': [
            (k, f'{k} {v["name"]}', v['doc'].split('；')[0].split('。')[0]) for k, v in STYLES.items() if isinstance(v, dict)]},
        {'key': 'audience', 'title': '受众与场合', 'default': 'dept', 'options': [
            ('mgmt', '管理层汇报', '结论先行，少而大的数字'), ('dept', '部门内部', '过程与细节都要'),
            ('ext', '对外 / 专家会', '来源与口径写全'), ('read', '发给人自看', '自解释，少依赖讲者')]},
        {'key': 'motion', 'title': '动效', 'default': 'auto', 'options': [
            ('auto', '入场 + 分步演示', '讲流程、计划、数据的页按 scene 推进（15 DEMO）'),
            ('light', '只做入场', '卡片与图表依次出现，不做演示舞台'),
            ('none', '静态', '打印、邮件附件')]},
        {'key': 'scenes', 'title': '包含的临床场景', 'note': '可多选；不确定就留空，按材料判断', 'multi': True, 'default': [], 'ask': False,
         'options': [(k, v[0], v[5]) for k, v in SCENES.items()]},
        {'key': 'pages', 'title': '页数或时长', 'text': True, 'default': '约 10 页 · 15 分钟', 'ask': False},
        {'key': 'note', 'title': '备注', 'text': True, 'default': '', 'ask': False},
    ]

def _prefill(path):
    return json.loads(Path(path).read_text(encoding='utf-8')) if path else {}

# ---------------------------------------------------------------- ask (AskUserQuestion batches)
def ask(detected=None, pre=None):
    pre = pre or {}; qs = [q for q in questions(detected) if q.get('ask', True) and q['key'] not in pre]
    # questions that depend on an answer already given are dropped; otherwise they say when they apply
    if 'track' in pre: qs = [q for q in qs if not q.get('when') or pre['track'] in q['when']]
    if pre.get('track') in ('site', 'stream') or pre.get('route') == 'flagship': qs = [q for q in qs if not q.get('when_route')]
    out = []
    for q in qs:
        cond = '' if 'track' in pre else '仅 PPTX / HTML-PPT 回答；' if q.get('when') else '仅常规路线回答；' if q.get('when_route') else ''
        opts = q['options'][:4]; d = q['default']
        opts = sorted(opts, key=lambda o: o[0] != d)   # the recommended / default option first
        note = cond + (q.get('note') or '')
        out.append({'question': f'{q["title"]}？' + (f'（{note.rstrip("；")}）' if note else ''), 'header': q['title'][:12], 'multiSelect': bool(q.get('multi')),
                    'options': [{'label': lab + ('（推荐）' if k == d else ''), 'description': desc} for k, lab, desc in opts], 'key': q['key'],
                    'values': {lab + ('（推荐）' if k == d else ''): k for k, lab, _ in opts}})
    return [out[i:i + 4] for i in range(0, len(out), 4)]

# ---------------------------------------------------------------- apply
def apply(ans, detected=None):
    qs = {q['key']: q for q in questions(detected)}; err = []
    for k, q in qs.items():
        if q.get('text') or k not in ans: continue
        allowed = {o[0] for o in q['options']}; v = ans[k]
        if q.get('multi'):
            if not isinstance(v, list) or set(v) - allowed: err.append(f'{k}: {v} 不在 {sorted(allowed)}')
        elif v not in allowed: err.append(f'{k}: {v} 不在 {sorted(allowed)}')
    track = ans.get('track')
    if track not in {o[0] for o in qs['track']['options']}: err.append('缺 track（交付形式）')
    slides = track in ('pptx', 'htmlppt')
    if slides and 'route' not in ans: err.append('PPTX / HTML-PPT 必须回答 route（14 FLAG-01）')
    if slides and 'image' not in ans: err.append('PPTX / HTML-PPT 必须回答 image（04 IMG-07）')
    if ans.get('image') == 'other' and not ans.get('note'): err.append('image=other 时在 note 里写明生图方式')
    if err: raise ValueError('；'.join(err))
    route = ans.get('route', 'regular') if slides else 'regular'; flag = route == 'flagship'; scenes = ans.get('scenes') or []
    feats = {'notes'} if slides else set()
    if ans.get('motion', 'auto') != 'none' and track == 'pptx': feats.add('motion')
    if scenes: feats.add('charts')
    if 'program' in scenes: feats.add('gantt')
    cmd = f'python3 "$KZ_DIR/tools/context_pack.py" --track {track}' + (' --route flagship' if flag else '') + ' --stage bootstrap' + (f' --features {",".join(sorted(feats))}' if feats else '')
    plan = {'track': track}
    if slides:
        plan['route'] = route
        plan['image_capability'] = {'mode': ans['image'], 'detail': ans.get('note') if ans['image'] == 'other' else (detected or '')}
    prod = {k: {'template': SCENES[k][1], 'demo': SCENES[k][2], 'stage': SCENES[k][3], 'flag_pptx': SCENES[k][4]} for k in scenes}
    use = {k: ((v['flag_pptx'] if track == 'pptx' else v['stage']) if flag else None) or v['template'] for k, v in prod.items()}   # no flagship product → the regular template
    out = {'page_plan': plan, 'context_pack': cmd, 'scenes': prod, 'use': use, 'audience': ans.get('audience', 'dept'), 'motion': ans.get('motion', 'auto'),
           'pages': ans.get('pages', ''), 'background': None if flag or not slides else ans.get('background', STYLES['default'])}
    if track == 'pptx':
        out['ppt_master'] = {'image_usage': ['ai', 'provided'] if ans['image'] in ('generate', 'other') else ['provided'],
                             'image_ai_path': (detected or ans.get('note') or '') if ans['image'] != 'default_set' else None,
                             'animations': ans.get('motion', 'auto') != 'none',
                             'confirm': '确认页只核对康哲值（标题 32、副标题 24、注释 16 px）与上面两项，其余已由开工卡回答，不再逐项询问（adapters/ppt-master.md）'}
    if track == 'htmlppt':
        out['html_ppt'] = {'skip_questions': True, 'theme': None, 'scenes_by_keys': ans.get('motion', 'auto') == 'auto',
                           'confirm': 'html-ppt-skill 的主题、配色、字体与动画询问一律不再出现：主题与配色由 tokens 固定，动效由本答案决定（adapters/html-ppt.md）'}
    return out

# ---------------------------------------------------------------- html
CSS = """:root{--b:%(brand)s;--ink:%(ink)s;--body:%(body)s;--mut:%(muted)s;--paper:#FBF8F3}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 "PingFang SC","Microsoft YaHei",sans-serif;color:var(--body);background:var(--paper)}
.hdr{position:sticky;top:0;z-index:2;display:flex;align-items:center;gap:1rem;padding:.9rem 3.2vw;background:rgba(255,255,255,.86);backdrop-filter:blur(12px);border-bottom:1px solid #EEE6DA}
.hdr b{color:var(--ink);font-size:1.05rem}.hdr .meta{margin-left:auto;color:var(--mut);font-size:.9rem}
main{padding:1.6rem 3.2vw 7rem;display:grid;grid-template-columns:repeat(12,1fr);gap:1.1rem}
.intro{grid-column:1/-1}.intro h1{margin:.2rem 0;color:var(--ink);font-size:1.8rem}.intro .k{color:var(--b);font-weight:700}
.q{grid-column:span 6;background:#fff;border:1px solid #EFE6D9;border-radius:18px;padding:1.1rem 1.2rem;box-shadow:0 10px 30px rgba(120,80,30,.06)}
.q.wide{grid-column:1/-1}.q h2{margin:0 0 .7rem;font-size:1.05rem;color:var(--ink)}.q h2 small{font-weight:400;color:var(--mut);margin-left:.5rem}
.q[hidden]{display:none}.opts{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.7rem}
.opt{border:1.5px solid #EEE4D6;border-radius:14px;padding:.75rem .9rem;cursor:pointer;position:relative;background:#FFFDF9}
.opt b{display:block;color:var(--ink)}.opt span{font-size:.88rem;color:var(--mut)}
.opt.on{border-color:var(--b);background:#FFF6E8;box-shadow:0 0 0 3px rgba(255,153,0,.15)}.opt .rec{position:absolute;right:.6rem;top:.5rem;font-size:.75rem;color:var(--b);font-weight:700}
input,textarea{width:100%%;font:inherit;padding:.6rem .8rem;border:1.5px solid #EEE4D6;border-radius:12px;background:#FFFDF9}
.bar{position:fixed;left:0;right:0;bottom:0;display:flex;gap:.8rem;align-items:center;padding:.9rem 3.2vw;background:rgba(255,255,255,.92);border-top:1px solid #EEE6DA}
.bar .sum{flex:1;color:var(--mut);font-size:.9rem}.btn{font:inherit;border:0;border-radius:999px;padding:.6rem 1.3rem;background:var(--b);color:#fff;font-weight:700;cursor:pointer}
.btn.ghost{background:#fff;color:var(--ink);border:1.5px solid #E5D9C8}pre{grid-column:1/-1;white-space:pre-wrap;background:#fff;border:1px dashed var(--b);border-radius:14px;padding:1rem}
""" % {'brand': TOK['colors']['brand'], 'ink': TOK['colors']['ink'], 'body': TOK['colors']['body'], 'muted': TOK['colors']['muted']}

JS = """const Q=%s,A=%s;const st={};
const sel=(k,v)=>{const q=Q.find(x=>x.key===k);if(q.multi){const s=new Set(st[k]||[]);s.has(v)?s.delete(v):s.add(v);st[k]=[...s];}else st[k]=v;draw();};
function vis(q){if(q.when&&!q.when.includes(st.track))return false;if(q.when_route&&(!['pptx','htmlppt'].includes(st.track)||st.route!==q.when_route))return false;return true;}
function draw(){for(const q of Q){const el=document.querySelector(`[data-k="${q.key}"]`);el.hidden=!vis(q);
 el.querySelectorAll('.opt').forEach(o=>o.classList.toggle('on',q.multi?(st[q.key]||[]).includes(o.dataset.v):st[q.key]===o.dataset.v));}
 document.getElementById('sum').textContent=Q.filter(vis).filter(q=>!q.text).map(q=>q.title+'：'+[].concat(st[q.key]??[]).map(v=>(q.options.find(o=>o[0]===v)||[,v])[1]).join('、')||'—').join(' · ');}
function result(){const o={version:1};for(const q of Q){if(!vis(q))continue;if(q.text){o[q.key]=document.querySelector(`[data-k="${q.key}"] input`).value.trim();}else o[q.key]=st[q.key];}return o;}
for(const q of Q){st[q.key]=A[q.key]??q.default;}
document.querySelectorAll('.opt').forEach(o=>o.addEventListener('click',()=>sel(o.closest('.q').dataset.k,o.dataset.v)));
document.getElementById('def').onclick=()=>{for(const q of Q)if(!q.text)st[q.key]=q.default;draw();};
document.getElementById('ok').onclick=()=>{const r=JSON.stringify(result(),null,1);const p=document.getElementById('out');p.hidden=false;p.textContent=r;
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([r],{type:'application/json'}));a.download='kz-intake.json';a.click();p.scrollIntoView({behavior:'smooth'});};
draw();"""

def html(topic='', detected=None, pre=None):
    qs = questions(detected); pre = pre or {}; parts = []
    for i, q in enumerate(qs, 1):
        wide = ' wide' if q.get('multi') or q['key'] in ('track',) else ''
        head = f'<h2>{i} · {escape(q["title"])}' + (f'<small>{escape(q["note"])}</small>' if q.get('note') else '') + '</h2>'
        if q.get('text'):
            body = f'<input value="{escape(str(pre.get(q["key"], q["default"])))}" aria-label="{escape(q["title"])}">'
        else:
            body = '<div class="opts">' + ''.join(f'<div class="opt" data-v="{escape(k)}">' + ('<i class="rec">推荐</i>' if k == q['default'] else '')
                                                  + f'<b>{escape(lab)}</b><span>{escape(desc)}</span></div>' for k, lab, desc in q['options']) + '</div>'
        parts.append(f'<section class="q{wide}" data-k="{q["key"]}">{head}{body}</section>')
    data = [{k: v for k, v in q.items()} for q in qs]
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>康哲 Design · 开工卡</title><style>{CSS}</style></head><body>'
            '<header class="hdr"><b>康哲 Design · 开工卡</b><div class="meta">第 1 站 / 共 2 站 · 选完即开工，后面不再重复问</div></header>'
            f'<main><div class="intro"><div class="k">{escape(topic or "新任务")}</div><h1>先定这几项</h1>'
            '<p>这些选择会预填到 ppt-master / html-ppt 的确认页；拿不准的保持推荐值。点「确认」后会下载 kz-intake.json，并在页面底部显示同样的内容，可以直接复制回对话。</p></div>'
            + ''.join(parts) + '<pre id="out" hidden></pre></main>'
            '<div class="bar"><div class="sum" id="sum"></div><button class="btn ghost" id="def">全部用推荐</button><button class="btn" id="ok">确认，生成分页故事板 →</button></div>'
            f'<script>{JS % (json.dumps(data, ensure_ascii=False), json.dumps(pre, ensure_ascii=False))}</script></body></html>')

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0]); sub = ap.add_subparsers(dest='cmd', required=True)
    h = sub.add_parser('html'); h.add_argument('--out', required=True); h.add_argument('--topic', default=''); h.add_argument('--detected'); h.add_argument('--prefill')
    a = sub.add_parser('ask'); a.add_argument('--detected'); a.add_argument('--prefill')
    p = sub.add_parser('apply'); p.add_argument('answers'); p.add_argument('--detected')
    o = ap.parse_args(argv)
    if o.cmd == 'html':
        Path(o.out).write_text(html(o.topic, o.detected, _prefill(o.prefill)), encoding='utf-8'); print(o.out)
    elif o.cmd == 'ask':
        print(json.dumps(ask(o.detected, _prefill(o.prefill)), ensure_ascii=False, indent=1))
    else:
        try: print(json.dumps(apply(_prefill(o.answers), o.detected), ensure_ascii=False, indent=1))
        except ValueError as e: print(f'开工卡答案不完整：{e}', file=sys.stderr); return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())

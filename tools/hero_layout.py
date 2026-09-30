"""Fixed brand fragments only. Export/navigation remain owned by upstream engines."""
from pathlib import Path
from html import escape
import json
import unicodedata
ROOT=Path(__file__).resolve().parents[1]
T=json.loads((ROOT/'tokens/tokens.json').read_text())
def layout(kind, content):
    k=T['hero_layouts'][kind]; blocks=[];cards=[]
    def text(role, lines, rect, color='ink', bold=False, card_index=None):
        if isinstance(lines,str):lines=lines.splitlines()
        if lines is None:lines=[]
        if not isinstance(lines,list) or any(not isinstance(line,str) for line in lines):raise ValueError('文字必须为字符串或逐行字符串列表')
        if not lines or not any(line.strip() for line in lines):
            if role in {'cover_title','toc_title','section_title','ending_title','section_number','toc_number','toc_label'}:raise ValueError('必需标题/编号不能为空')
            return
        if any(not line.strip() for line in lines):raise ValueError('不能用空行填充固定文字框')
        size=T['type_px'][role]
        if len(lines)*size*1.25>rect[3]+.01:raise ValueError('固定文字框溢出，请精简或拆页，不能缩字')
        # A conservative routing guard, not native/font-shaped width certification.
        def em(line):return sum(0 if unicodedata.combining(c) else 1 if unicodedata.east_asian_width(c) in {'W','F'} else .5 for c in line)
        if rect[2]<=0 or any(em(line)*size>rect[2]+.01 for line in lines):raise ValueError('固定文字框横向容量不足，请精简或换行/拆页，不能裁字；最终仍须实际字体测量')
        block=dict(role=role,lines=lines,rect=rect,font_px=size,line_height=1.25,color=T['colors'][color],bold=bold)
        if card_index is not None:block['card_index']=card_index
        blocks.append(block)
    if kind=='cover':
        text('cover_title',content['title'],k['title'],bold=True)
        text('hero_subtitle',content.get('subtitle',''),k['subtitle'],'body')
        text('hero_meta',content.get('meta',''),k['meta'],'muted')
    elif kind=='section':
        text('section_number',content['number'],k['number'],'brand',True)
        text('section_title',content['title'],k['title'],bold=True)
    elif kind=='ending':
        text('ending_title',content['title'],k['title'],bold=True)
        text('hero_subtitle',content.get('subtitle',''),k['subtitle'],'body')
        text('hero_meta',content.get('meta',''),k['meta'],'muted')
    else:
        text('toc_title',content['title'],k['title'],bold=True)
        items=content['items'];n=len(items)
        if not 1<=n<=k['max_items']:raise ValueError('目录每页1至6项，更多必须拆页')
        gx,gy,gw,_=k['grid'];gap=k['gap'];cw=(gw-2*gap)/3
        for i,item in enumerate(items):
            row=i//3;col=i%3;count=min(3,n-row*3);x=gx+(gw-(count*cw+(count-1)*gap))/2+col*(cw+gap);y=gy+row*(k['row_height']+gap)
            cards.append([x,y,cw,k['row_height']])
            reading=k['reading']
            text('toc_number',f'{i+1:02d}',[x+reading['number_left'],y+reading['number_top'],reading['number_width'],reading['number_height']],'brand',True,card_index=i)
            text('toc_label',item['title'],[x+reading['label_left'],y+reading['label_top'],cw-reading['label_left']-reading['label_right'],reading['label_height']],bold=True,card_index=i)
            if str(item.get('description') or '').strip():
                text('toc_description',item['description'],[x+reading['description_left'],y+reading['description_top'],cw-reading['description_left']-reading['description_right'],reading['description_height']],'body',card_index=i)
    return k,blocks,cards

def html_fragment(kind,content,image,logo):
    k,blocks,cards=layout(kind,content)
    def box(r):return f'left:{r[0]:g}px;top:{r[1]:g}px;width:{r[2]:g}px;height:{r[3]:g}px;'
    out=[f'<div class="kz-fixed-hero" data-hero-layout="{k["id"]}" style="position:absolute;inset:0;overflow:hidden;background:#FBFCFD;">',f'<img aria-hidden="true" src="{escape(image,quote=True)}" style="position:absolute;{box(k["image"])}object-fit:contain;">',f'<img alt="康哲药业" src="{escape(logo,quote=True)}" style="position:absolute;{box(k["logo"])}object-fit:contain;filter:none;">']
    def text_html(b, origin=(0,0)):
        r=list(b['rect']);r[0]-=origin[0];r[1]-=origin[1]
        tag='h1' if b['role'] in ['cover_title','toc_title','section_title','ending_title'] else 'p'
        return f'<{tag} data-hero-role="{b["role"]}" style="position:absolute;{box(r)}margin:0;padding:0;border:0;font-family:var(--kz-font);font-size:{b["font_px"]}px;line-height:1.25;font-weight:{700 if b["bold"] else 400};color:{b["color"]};text-align:left;text-shadow:none;white-space:nowrap;">'+ '<br>'.join(escape(x) for x in b['lines'])+f'</{tag}>'
    card_roles={'toc_number','toc_label','toc_description'}
    for index,r in enumerate(cards):
        x,y,w,h=r
        out.append(f'<div data-kz-reveal style="position:absolute;{box(r)}transform-style:flat;"><div class="kz-float" style="width:100%;height:100%;"><div class="kz-card" data-kz-tilt="10" data-kz-light style="position:relative;width:100%;height:100%;padding:0;">')
        for b in blocks:
            if b.get('card_index')==index:
                out.append(text_html(b,(x,y)))
        out.append('</div></div></div>')
    for b in blocks:
        if b['role'] not in card_roles:out.append(text_html(b))
    return '\n'.join(out+['</div>'])

def svg_fragment(kind,content,image,logo):
    k,blocks,cards=layout(kind,content)
    def img(path,r,id):return f'<image id="{id}" data-pptx-role="{ "logo" if id=="logo" else "background"}" href="{escape(path,quote=True)}" x="{r[0]}" y="{r[1]}" width="{r[2]}" height="{r[3]}" preserveAspectRatio="xMidYMid meet"/>'
    # Decorative image bleed uses the root viewport; text capacity is checked above.
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" font-family="Microsoft YaHei, Arial" data-pptx-page-role="'+('cover' if kind=='cover' else 'section' if kind=='section' else 'ending' if kind=='ending' else 'content')+'">','<defs><filter id="shadow"><feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#0F1115" flood-opacity="0.10"/></filter></defs>','<rect width="1280" height="720" fill="#FBFCFD"/>',img(image,k['image'],'hero-image'),img(logo,k['logo'],'logo')]
    for i,(x,y,w,h) in enumerate(cards):out.extend([f'<rect id="card-{i}" x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="#FFFFFF" fill-opacity="{T["glass"]["face_alpha"]}" stroke="#B5B4B1" stroke-opacity=".32" stroke-width="1" filter="url(#shadow)"/>',f'<path d="M{x+24} {y+2}h{w*.25}" stroke="#FFFFFF" stroke-opacity=".9" stroke-width="1.5"/>'])
    for i,b in enumerate(blocks):
        x,y,w,h=b['rect'];f=b['font_px'];lines=b['lines']
        out.append(f'<g id="hero-text-{i}" data-pptx-bounds="{x} {y} {w} {h}"><text x="{x}" y="{y+f*.9}" font-size="{f}" font-weight="{700 if b["bold"] else 400}" fill="{b["color"]}">')
        for j,line in enumerate(lines):out.append(f'<tspan x="{x}" dy="{0 if j==0 else f*1.25}">{escape(line)}</tspan>')
        out.append('</text></g>')
    return '\n'.join(out+['</svg>'])

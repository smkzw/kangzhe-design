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
    out=[f'<div class="kz-fixed-hero" data-hero-layout="{k["id"]}" style="position:absolute;inset:0;overflow:hidden;background:#FBFCFD;">',f'<img aria-hidden="true" src="{escape(image,quote=True)}" style="position:absolute;{box(k["image"])}object-fit:cover;">',f'<img alt="康哲药业" src="{escape(logo,quote=True)}" style="position:absolute;{box(k["logo"])}object-fit:contain;filter:none;">']
    def text_html(b, origin=(0,0)):
        r=list(b['rect']);r[0]-=origin[0];r[1]-=origin[1]
        tag='h1' if b['role'] in ['cover_title','toc_title','section_title','ending_title'] else 'p'
        return f'<{tag} data-hero-role="{b["role"]}" style="position:absolute;{box(r)}margin:0;padding:0;border:0;font-family:var(--kz-font);font-size:{b["font_px"]}px;line-height:1.25;font-weight:{700 if b["bold"] else 400};color:{b["color"]};text-align:left;text-shadow:none;white-space:nowrap;">'+ '<br>'.join(escape(x) for x in b['lines'])+f'</{tag}>'
    card_roles={'toc_number','toc_label','toc_description'}
    for index,r in enumerate(cards):
        x,y,w,h=r
        hero_tilt=T['motion']['tilt']['hero_max_deg']
        out.append(f'<div data-kz-reveal style="position:absolute;{box(r)}transform-style:flat;"><div class="kz-float" style="width:100%;height:100%;--kz-float-index:{index};"><div class="kz-card" data-kz-tilt="{hero_tilt}" data-kz-light style="position:relative;width:100%;height:100%;padding:0;">')
        for b in blocks:
            if b.get('card_index')==index:
                out.append(text_html(b,(x,y)))
        out.append('</div></div></div>')
    for b in blocks:
        if b['role'] not in card_roles:out.append(text_html(b))
    return '\n'.join(out+['</div>'])

def _shadow_filter():
    # ppt-master converts one direct feDropShadow per object to a native outerShdw (alpha ×≈0.75 on export).
    sh=T['elevation']['pptx']['rest'];color=T['elevation']['pptx']['color']
    return f'<filter id="shadow"><feDropShadow dx="{sh["dx"]}" dy="{sh["dy"]}" stdDeviation="{sh["std_deviation"]}" flood-color="{color}" flood-opacity="{sh["alpha"]}"/></filter>'

def _face_gradient():
    stops=''.join(f'<stop offset="{v["offset"]}" stop-color="{v["color"]}" stop-opacity="{v["alpha"]}"/>' for v in T['glass']['face_gradient'])
    return f'<linearGradient id="kz-face" x1="0" y1="0" x2="1" y2="1">{stops}</linearGradient>'

def html_fluid_fragment(kind,content,image,logo):
    """Same fixed layout for html-ppt fluid decks (adapters/html-ppt.md): geometry in --kz-u, type in --kz-un.
    Left text anchors keep their 1280-basis offsets; right-side logos follow the right anchor; the TOC row
    spreads across the content width; hero titles enter in reading order. No second fit or navigation."""
    k,blocks,cards=layout(kind,content);W=T['hero_layouts']['canvas'][0]
    u=lambda n:f'calc({n:g} * var(--kz-u))'
    def place(r,anchor_right=False):
        x,y,w,h=r
        if anchor_right:return f'right:{u(W-x-w)};top:{u(y)};width:{u(w)};height:{u(h)};'
        return f'left:{u(x)};top:{u(y)};width:min({u(w)},calc(100% - {(x+(W-x-w)):g} * var(--kz-u)));height:{u(h)};'
    order={'cover_title':0,'section_number':0,'ending_title':0,'toc_title':0,'section_title':1,'hero_subtitle':1,'hero_meta':2}
    def text_html(b,inside_card=False,origin=(0,0)):
        tag='h1' if b['role'] in ['cover_title','toc_title','section_title','ending_title'] else 'p'
        x,y,w,h=b['rect'];x-=origin[0];y-=origin[1]
        geo=f'left:{u(x)};top:{u(y)};right:{u(T["hero_layouts"]["toc"]["reading"]["label_right"])};height:{u(h)};' if inside_card else place([x,y,w,h])
        reveal='' if inside_card else f' data-kz-reveal data-kz-order="{order.get(b["role"],1)}"'
        return f'<{tag} data-hero-role="{b["role"]}"{reveal} style="position:absolute;{geo}margin:0;padding:0;border:0;font-family:var(--kz-font);font-size:calc({b["font_px"]}px * var(--kz-un,1));line-height:1.25;font-weight:{700 if b["bold"] else 400};color:{b["color"]};text-align:left;text-shadow:none;white-space:nowrap;">'+'<br>'.join(escape(x) for x in b['lines'])+f'</{tag}>'
    ix,iy,iw,ih=k['image']
    out=[f'<div class="kz-fixed-hero kz-hero-fluid" data-hero-layout="{k["id"]}" style="position:absolute;inset:0;overflow:hidden;background:#FBFCFD;">',
         # Wide fluid view: the image always covers the slide (no top band). A basis rect pushed down (y>0) means the
         # subject sits low, so the wide crop is anchored to the bottom; review the crop per aspect (04 IMG-03).
         f'<img class="kz-hero-image" aria-hidden="true" src="{escape(image,quote=True)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% {"100%" if iy>0 else "50%"};">',
         f'<img alt="康哲药业" src="{escape(logo,quote=True)}" style="position:absolute;{place(k["logo"],k["logo"][0]>W/2)}object-fit:contain;filter:none;">']
    if cards:
        g=k['grid'];gap=k['gap'];hero_tilt=T['motion']['tilt']['hero_max_deg']
        out.append(f'<div class="kz-hero-toc" style="position:absolute;left:{u(g[0])};right:{u(W-g[0]-g[2])};top:{u(g[1])};display:flex;flex-wrap:wrap;justify-content:center;gap:{u(gap)};">')
        for index,(x,y,w,h) in enumerate(cards):
            out.append(f'<div data-kz-reveal data-kz-order="{1+index}" style="position:relative;flex:0 0 calc((100% - {2*gap:g} * var(--kz-u)) / 3);height:{u(h)};"><div class="kz-float" style="width:100%;height:100%;--kz-float-index:{index};"><div class="kz-card" data-kz-tilt="{hero_tilt}" data-kz-light style="position:relative;width:100%;height:100%;padding:0;">')
            for b in blocks:
                if b.get('card_index')==index:out.append(text_html(b,True,(x,y)))
            out.append('</div></div></div>')
        out.append('</div>')
    for b in blocks:
        if 'card_index' not in b:out.append(text_html(b))
    return '\n'.join(out+['</div>'])

def svg_fragment(kind,content,image,logo):
    k,blocks,cards=layout(kind,content)
    def img(path,r,id):return f'<image id="{id}" data-pptx-role="{ "logo" if id=="logo" else "background"}" href="{escape(path,quote=True)}" x="{r[0]}" y="{r[1]}" width="{r[2]}" height="{r[3]}" preserveAspectRatio="{"xMidYMid meet" if id=="logo" else "xMidYMid slice"}"/>'
    # Decorative image bleed uses the root viewport; text capacity is checked above.
    role={'cover':'cover','toc':'toc','section':'section','ending':'ending'}[kind]
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" lang="zh-CN" font-family="Microsoft YaHei, Arial" data-pptx-page-role="'+role+'">','<defs>'+_shadow_filter()+_face_gradient()+'</defs>','<rect id="page-bg" width="1280" height="720" fill="#FBFCFD"/>',img(image,k['image'],'hero-image'),img(logo,k['logo'],'logo')]
    g=T['glass']
    def text(b):
        x,y,w,h=b['rect'];f=b['font_px']
        s=[f'<text x="{x:g}" y="{y+f*.9:g}" font-size="{f:g}" font-weight="{"bold" if b["bold"] else "normal"}" fill="{b["color"]}">']
        s+=[f'<tspan x="{x:g}" dy="{0 if j==0 else f*1.25:g}">{escape(line)}</tspan>' for j,line in enumerate(b['lines'])]
        return ''.join(s)+'</text>'
    # A TOC card and its number, label and description are one editable and animatable unit (one root group).
    for i,(x,y,w,h) in enumerate(cards):
        out.append(f'<g id="toc-card-{i+1}" data-pptx-bounds="{x:.2f} {y:g} {w:.2f} {h:g}">'
                   f'<rect x="{x:.2f}" y="{y:g}" width="{w:.2f}" height="{h:g}" rx="{g["radius"]}" fill="url(#kz-face)" stroke="{g["border_color"]}" stroke-opacity="{g["border_alpha"]}" stroke-width="1" filter="url(#shadow)"/>'
                   f'<path d="M{x+24:.2f} {y+2:g}h{w*g["highlight_extent_max"]:.1f}" stroke="#FFFFFF" stroke-opacity="0.9" stroke-width="1.5"/>'
                   +''.join(text(b) for b in blocks if b.get('card_index')==i)+'</g>')
    for i,b in enumerate(blocks):
        if b.get('card_index') is not None:continue
        x,y,w,h=b['rect']
        out.append(f'<g id="hero-{b["role"].replace("_","-")}" data-pptx-bounds="{x:g} {y:g} {w:g} {h:g}">'+text(b)+'</g>')
    return '\n'.join(out+['</svg>'])

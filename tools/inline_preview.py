"""Inline a trusted local reference HTML for policy-restricted browser tests.
This does not claim HTTP/file:// or CSP equivalence. Never use untrusted input.
"""
from pathlib import Path
import re,base64,mimetypes,argparse

def inline_html(path: Path, root: Path|None=None) -> str:
    path=path.resolve();root=(root or path.parent.parent).resolve()
    def local(ref):
        if re.match(r'^(https?:|//|data:)',ref): raise ValueError('Reference must be local: '+ref)
        p=(path.parent/ref.split('?')[0].split('#')[0]).resolve()
        if not p.is_relative_to(root):raise ValueError('Asset escapes package root: '+ref)
        return p
    text=path.read_text(encoding='utf-8')
    def css(m):return '<style>\n'+local(m.group(1)).read_text(encoding='utf-8')+'\n</style>'
    def js(m):return '<script>\n'+local(m.group(1)).read_text(encoding='utf-8').replace('</script','<\\/script')+'\n</script>'
    text=re.sub(r'<link\s+rel="stylesheet"\s+href="([^"]+)"\s*>',css,text)
    def img(m):
        p=local(m.group(2));mime=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
        return m.group(1)+'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()+m.group(3)
    text=re.sub(r'(<img[^>]*\ssrc=")([^"]+)(")',img,text)
    text=re.sub(r'<script\s+src="([^"]+)"\s*>\s*</script>',js,text)
    return text
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.write_text(inline_html(a.input),encoding='utf-8')

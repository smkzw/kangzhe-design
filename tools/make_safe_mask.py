"""Generate layout masks, not AI images. White = protected/quiet, black = usable."""
from pathlib import Path
import json,argparse
from PIL import Image,ImageDraw

def make(plan,index,out):
 w,h=map(int,plan['canvas']);p=plan['pages'][index];im=Image.new('RGB',(w,h),'black');d=ImageDraw.Draw(im)
 for r in p['protected_regions']:
  x,y,rw,rh=r['rect'];m=max(16,r.get('motion_margin',0));d.rectangle([max(0,x-m),max(0,y-m),min(w,x+rw+m),min(h,y+rh+m)],fill='white')
 im.save(out)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('plan',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--page-index',type=int,default=0);a=ap.parse_args();make(json.loads(a.plan.read_text()),a.page_index,a.out)

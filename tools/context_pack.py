"""Produce a minimal explicit file-reading index, not an alternative rule set."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def files(track,features):
 base=['SKILL.md','tokens/tokens.json']+[f'design_specs/{x}.md' for x in ['00-authority','01-core','02-liquid-glass','03-typography-language','04-image-pipeline','tracks-'+track,'10-quality-gates']]
 if track in ['pptx','htmlppt']:base+=['design_specs/11-hero-layouts.md']
 if track=='pptx':base+=['adapters/ppt-master.md']
 if track=='htmlppt':base+=['adapters/html-ppt.md']
 if track in ['site','stream']:features.add('film');features.add('drilldown')
 table={'charts':'05-charts','film':'06-motion-film','drilldown':'07-drilldown','gantt':'08-gantt','notes':'09-speaker-notes'}
 for f in sorted(features):
  if f not in table:raise ValueError('Unknown feature: '+f)
  base+=['design_specs/'+table[f]+'.md']
 if 'gantt' in features and 'charts' not in features:base+=['design_specs/05-charts.md']
 for f in base:
  if not (ROOT/f).is_file():raise FileNotFoundError(f)
 return list(dict.fromkeys(base))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--track',choices=['pptx','htmlppt','site','stream'],required=True);ap.add_argument('--features',default='');a=ap.parse_args();fs=files(a.track,set(filter(None,a.features.split(','))));print(json.dumps({'track':a.track,'read_files':fs,'note':'Read the actual owner files. Index is not a substitute.'},ensure_ascii=False,indent=2))

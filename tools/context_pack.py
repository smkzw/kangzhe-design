"""Produce a minimal explicit file-reading index, not an alternative rule set."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def files(track,features):
 base=['SKILL.md','tokens/tokens.json']+[f'design_specs/{x}.md' for x in ['00-authority','01-core','02-liquid-glass','03-typography-language','04-image-pipeline','tracks-'+track,'10-quality-gates']]
 if track in ['pptx','htmlppt']:base+=['design_specs/11-hero-layouts.md']
 if track=='pptx':base+=['adapters/ppt-master.md']
 if track=='htmlppt':base+=['adapters/html-ppt.md']
 if track in ['htmlppt','site','stream']:features.add('film')
 if track in ['site','stream']:features.add('drilldown')
 table={'charts':'05-charts','film':'06-motion-film','drilldown':'07-drilldown','gantt':'08-gantt','notes':'09-speaker-notes'}
 for f in sorted(features):
  if f not in table:raise ValueError('Unknown feature: '+f)
  base+=['design_specs/'+table[f]+'.md']
 if 'gantt' in features and 'charts' not in features:base+=['design_specs/05-charts.md']
 for f in base:
  if not (ROOT/f).is_file():raise FileNotFoundError(f)
 return list(dict.fromkeys(base))

STAGES=('bootstrap','plan','assets','author','verify')
def index(track,features,stage='all',seen=None):
 """Route owner paths, not copied rules or a production acceptance verdict."""
 complete=files(track,set(features))
 if stage=='all': selected=complete
 elif stage=='bootstrap':
  selected=['SKILL.md','design_specs/00-authority.md','design_specs/tracks-'+track+'.md']
  if track=='pptx':selected+=['adapters/ppt-master.md']
  if track=='htmlppt':selected+=['adapters/html-ppt.md']
 elif stage=='plan':
  selected=[p for p in complete if p.startswith(('tokens/','design_specs/')) and not p.endswith('10-quality-gates.md')]
  selected+=['schemas/page-plan.schema.json','tools/qc_plan.py']
 elif stage=='assets':
  selected=['design_specs/04-image-pipeline.md','schemas/asset-manifest.schema.json','tools/qc_plan.py']
 elif stage=='author':
  selected=['tokens/tokens.json','runtime/API.md'] if track!='pptx' else ['tokens/tokens.json','adapters/ppt-master.md']
  if track=='htmlppt':selected+=['adapters/html-ppt.md']
  if track in ['pptx','htmlppt']:selected+=['tools/brand_fragments.py','tools/hero_layout.py']
 elif stage=='verify':selected=complete+['tools/qc_plan.py']
 else:raise ValueError('Unknown stage: '+stage)
 selected=list(dict.fromkeys(selected));owners=[]
 for p in selected:
  data=(ROOT/p).read_bytes();sha=hashlib.sha256(data).hexdigest()
  owners.append({'path':p,'sha256':sha,'bytes':len(data),'needs_read':(seen or {}).get(p)!=sha})
 pos=STAGES.index(stage) if stage in STAGES else None
 return {'track':track,'stage':stage,'read_files':selected,'owners':owners,
         'fingerprints':{o['path']:o['sha256'] for o in owners},
         'prerequisite_stages':list(STAGES[:pos]) if pos is not None else [],
         'next_stage':STAGES[pos+1] if pos is not None and pos+1<len(STAGES) else None,
         'scope':'reading index only; no stage or artifact is accepted by this output',
         'note':'Earlier owner requirements remain active. Hash matches permit reuse only when actually read in the same compatible session; final verification retains every applicable owner. Read implementation definitions when the public API is insufficient, not whole unrelated sources.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--track',choices=['pptx','htmlppt','site','stream'],required=True);ap.add_argument('--features',default='');ap.add_argument('--stage',choices=['all',*STAGES],default='all');ap.add_argument('--seen',type=Path,help='JSON {"fingerprints": {relative_owner_path: actually_read_sha256}}');a=ap.parse_args()
 seen=json.loads(a.seen.read_text())['fingerprints'] if a.seen else None
 if seen is not None and (not isinstance(seen,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in seen.items())):ap.error('--seen fingerprints must map paths to string hashes')
 print(json.dumps(index(a.track,set(filter(None,a.features.split(','))),a.stage,seen),ensure_ascii=False,indent=2))

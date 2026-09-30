"""Workflow boundaries: no loss of final owners, no stale read reuse."""
import hashlib,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from context_pack import index,files,STAGES
class ContextRouting(unittest.TestCase):
 def test_final_verification_preserves_all_applicable_owners(self):
  for track in ('pptx','htmlppt','site','stream'):
   features={'charts','gantt','notes','drilldown'}
   old=set(files(track,features.copy()))
   stages={s:index(track,features,s) for s in STAGES}
   self.assertTrue(old.issubset(set(stages['verify']['read_files'])))
   self.assertTrue(old.issubset(set().union(*(set(v['read_files']) for v in stages.values()))))
   self.assertEqual(stages['verify']['prerequisite_stages'],list(STAGES[:-1]))
   for v in stages.values():
    for o in v['owners']:
     self.assertEqual(o['sha256'],hashlib.sha256((ROOT/o['path']).read_bytes()).hexdigest())
 def test_legacy_read_list_is_preserved(self):
  for track in ('pptx','htmlppt','site','stream'):
   self.assertEqual(index(track,{'charts'})['read_files'],files(track,{'charts'}))
 def test_unchanged_read_owner_only_reused_by_exact_hash(self):
  first=index('htmlppt',{'charts'},'author')
  same=index('htmlppt',{'charts'},'author',first['fingerprints'])
  self.assertTrue(all(not o['needs_read'] for o in same['owners']))
  seen=first['fingerprints'].copy();seen['runtime/API.md']='0'*64
  changed=index('htmlppt',{'charts'},'author',seen)
  self.assertEqual([o['path'] for o in changed['owners'] if o['needs_read']],['runtime/API.md'])
  fresh=index('htmlppt',{'charts'},'author')
  self.assertTrue(all(o['needs_read'] for o in fresh['owners']))
 def test_engine_boundaries_and_unknown_features(self):
  ppt=index('pptx',set(),'author')['read_files'];html=index('htmlppt',set(),'author')['read_files']
  self.assertIn('adapters/ppt-master.md',ppt);self.assertNotIn('runtime/API.md',ppt)
  self.assertIn('adapters/html-ppt.md',html);self.assertIn('runtime/API.md',html)
  with self.assertRaisesRegex(ValueError,'Unknown feature'):index('site',{'invented'},'bootstrap')
if __name__=='__main__':unittest.main(verbosity=2)

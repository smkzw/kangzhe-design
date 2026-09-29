"""Guard exact native copying and refusal to change unrelated slide content."""
from pathlib import Path
from xml.dom import minidom as D
import json,sys,tempfile,unittest,zipfile
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from bind_header_mark_pptx import bind,signature,nodes,P,A
from brand_fragments import facets
class HeaderMarkTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.src=self.root/'upstream.pptx';self.dst=self.root/'result.pptx'
  self.approved=list(nodes(D.parse(str(R/'assets/header-mark/source-native.xml')),P,'sp'))
  self.xml='<p:sld xmlns:p="'+P+'" xmlns:a="'+A+'"><p:cSld><p:spTree>'+''.join(s.toxml() for s in self.approved)+'</p:spTree></p:cSld></p:sld>'
  self.plan={'pages':[{'slide':1,'replace_shape_ids':[61,62,63,64]}]}
 def pack(self,xml=None):
  with zipfile.ZipFile(self.src,'w') as z:
   z.writestr('ppt/slides/slide1.xml',xml or self.xml);z.writestr('ppt/presentation.xml','<p:presentation xmlns:p="'+P+'"><p:sldSz cx="12192000" cy="6858000"/></p:presentation>');z.writestr('unrelated.bin',b'\x00KEEP\xff')
 def test_exact_shape_copy_and_unrelated_part(self):
  self.pack();receipt=bind(self.src,self.dst,self.plan)
  with zipfile.ZipFile(self.dst) as z:
   shapes=list(nodes(D.parseString(z.read('ppt/slides/slide1.xml')),P,'sp'))
   self.assertEqual([signature(n) for n in shapes],[signature(n) for n in self.approved]);self.assertEqual(z.read('unrelated.bin'),b'\x00KEEP\xff')
   ids=[nodes(n,P,'cNvPr')[0].getAttribute('id') for n in shapes];self.assertEqual(len(ids),len(set(ids)))
  self.assertEqual(receipt['changed_parts'],['ppt/slides/slide1.xml'])
 def test_refuses_missing_and_text_ids(self):
  self.pack()
  with self.assertRaises(ValueError):bind(self.src,self.dst,{'pages':[{'slide':1,'replace_shape_ids':[999]}]})
  self.pack(self.xml.replace('<a:p/>','<a:p><a:r><a:t>Do not delete</a:t></a:r></a:p>',1))
  # The reference may use expanded empty paragraphs; inject text reliably.
  d=D.parseString(self.xml);t=d.createElementNS(A,'a:t');t.appendChild(d.createTextNode('Do not delete'));nodes(d,P,'sp')[0].appendChild(t);self.pack(d.toxml())
  with self.assertRaisesRegex(ValueError,'text'):bind(self.src,self.dst,self.plan)
  self.assertFalse(self.dst.exists())
 def test_refuses_overwriting_source(self):
  self.pack()
  with self.assertRaises(ValueError):bind(self.src,self.src,self.plan)
 def test_group_transform_is_not_silently_accepted(self):
  start='<p:grpSp><p:grpSpPr><a:xfrm><a:off x="1" y="0"/><a:ext cx="100" cy="100"/><a:chOff x="0" y="0"/><a:chExt cx="100" cy="100"/></a:xfrm></p:grpSpPr>'
  self.pack(self.xml.replace('<p:spTree>','<p:spTree>'+start).replace('</p:spTree>','</p:grpSp></p:spTree>'))
  with self.assertRaisesRegex(ValueError,'Non-identity'):bind(self.src,self.dst,self.plan)
 def test_svg_uses_same_four_shapes_one_float_group(self):
  s=facets();self.assertEqual(s.count('data-kz-source-shape='),4);self.assertEqual(s.count('class="kz-float"'),1)
  self.assertLess(s.index('kz-facet-o-candy'),s.index('kz-facet-y-candy'));self.assertNotIn('glint',s);self.assertNotIn('class="kz-float"',facets(native=True))
if __name__=='__main__':unittest.main()

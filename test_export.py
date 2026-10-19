import unittest,copy,json
from export_public_scanner import public_results

class ExportTest(unittest.TestCase):
 def setUp(self):
  self.base={'generated_at':'2026-10-16T23:48:23+00:00','stocks':[{'symbol':'MSFT','as_of':'2026-10-16','quality_score':80,'close':123,'breakout':{'signal':True,'volume_confirmed':True,'trigger':123}}],'errors':[]}
 def test_threshold(self):
  self.assertEqual(public_results(self.base)['selection'],[])
 def test_signal_and_privacy(self):
  for score,signal,volume,status in [(80.1,True,True,'WATCH'),(90,True,True,'WATCH'),(90.1,False,True,'WATCH'),(95,True,False,'WATCH'),(95,True,True,'BREAKOUT')]:
   d=copy.deepcopy(self.base);s=d['stocks'][0];s['quality_score']=score;s['breakout'].update(signal=signal,volume_confirmed=volume)
   r=public_results(d);self.assertEqual(r['selection'][0]['status'],status)
   self.assertEqual(set(r['selection'][0]),{'symbol','name','score','status','as_of'})
 def test_invalid(self):
  for score in [True,float('nan'),101,-1]:
   d=copy.deepcopy(self.base);d['stocks'][0]['quality_score']=score
   with self.assertRaises(ValueError):public_results(d)
 def test_top_three(self):
  d=copy.deepcopy(self.base);d['stocks']=[]
  for i,sym in enumerate(['AMD','MSFT','NVDA','PLTR']):d['stocks'].append({'symbol':sym,'as_of':'2026-10-16','quality_score':81+i})
  r=public_results(d);self.assertEqual(len(r['selection']),3);self.assertEqual(r['counts']['watch'],4);self.assertEqual(r['selection'][0]['symbol'],'PLTR')
 def test_partial(self):
  self.base['stocks'][0]['quality_score']=None
  with self.assertRaises(ValueError):public_results(self.base)
if __name__=='__main__':unittest.main()

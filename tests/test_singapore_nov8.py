import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NewSingaporeEpisode(unittest.TestCase):
 def test_supplied_text_and_caption_limits(self):
  ep=json.loads((ROOT/'episodes/singapore-economy/2026-11-08-ja.json').read_text())
  raw=json.loads((ROOT/'editorial/singapore-economy/2026-11-08-provided-script.json').read_text())
  for part,item in enumerate([raw['intro'],*raw['items'],raw['outro']]):
   text=''.join(l['show'] for l in item['lines']) if 'lines'in item else item['show']
   self.assertEqual(text,''.join(c['show'] for c in ep['lines_timed'] if c['part']==part))
  self.assertTrue(all(len(c['show'])<=30 and c['end']-c['start']>=1 for c in ep['lines_timed']))
  self.assertTrue(all(a['end']<=b['start'] for a,b in zip(ep['lines_timed'],ep['lines_timed'][1:])))
  self.assertEqual(ep['date'],'2026-11-08')
  self.assertEqual(ep['broadcast_date'],'2026-11-08')
  self.assertEqual(ep['news_date'],'2026-11-07')
  self.assertEqual(ep['speakers']['metan']['credit'],'音声：Meticulous Pen (Muse)')
  self.assertEqual(ep['segments'][-1]['speaker'],'takehiro')
  self.assertTrue((ROOT/'episodes/singapore-economy/2026-11-06-ja.json').is_file())
  self.assertEqual(len(ep['news']),4)
  self.assertTrue(all(len(n['points'])==len(n['details']) for n in ep['news']))
  self.assertTrue(all(s['url'].startswith('https://') for n in ep['news'] for s in n['sources']))
if __name__=='__main__':unittest.main()

"""Subtitle boundaries must match generated speech without changing its text."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('radio_voicevox',Path(__file__).resolve().parents[1]/'tools/generate_voicevox.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def query(text):
    return {'speedScale':1.07,'prePhonemeLength':.08,'postPhonemeLength':.12,'accent_phrases':[{'moras':[{'text':x,'vowel_length':.12,'consonant_length':.04} for x in text],'pause_mora':None}]}
class Client:
    def query(self,text,speaker):return 'cached',query(text)
class TimingTests(unittest.TestCase):
    def test_caption_text_and_audio_endpoints_are_preserved(self):
        line={'show':'アイウエオ','say':'アイウエオ','captions':[{'show':'アイウ','say':'アイウ'},{'show':'エオ','say':'エオ'}]}
        result=module.caption_bounds(line,query(line['say']),1.2,Client(),2)
        self.assertEqual(''.join(x[0] for x in result),line['show'])
        self.assertEqual(result[0][1],0)
        self.assertEqual(result[-1][2],1.2)
        self.assertGreater(result[0][2],0)
        self.assertEqual(result[0][2],result[1][1])
    def test_caption_mismatch_is_rejected(self):
        line={'show':'アイ','say':'アイ','captions':[{'show':'ア','say':'ア'}]}
        with self.assertRaisesRegex(ValueError,'differs'):
            module.caption_bounds(line,query('アイ'),1,Client(),2)
    def test_existing_episode_is_protected_before_engine_calls(self):
        import argparse,tempfile,json
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'draft.json';p.write_text(json.dumps({'date':'2026-11-06','lang':'ja'}))
            with self.assertRaisesRegex(ValueError,'Existing episode protected'):
                module.generate(argparse.Namespace(input=p,replace=False))
if __name__=='__main__':unittest.main()

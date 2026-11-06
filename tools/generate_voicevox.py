"""Generate a complete radio episode from an editorial draft using local VOICEVOX.

Usage: python3 tools/generate_voicevox.py editorial/YYYY-MM-DD-aviation-script.json
Each line may contain short captions [{show, say}] which must join to line.show.
Saves audio only under ignored audio/, and derives chapter/subtitle timing from synthesis.
Existing published episodes cannot be replaced unless --replace is explicitly supplied.
"""
from __future__ import annotations
import argparse,bisect,hashlib,io,json,subprocess,tempfile,urllib.parse,urllib.request,wave,unicodedata
from pathlib import Path

RATE=24000
ROOT=Path(__file__).resolve().parents[1]

def normalize(s):
    return ''.join(c for c in unicodedata.normalize('NFKC',s) if '\u30a1'<=c<='\u30fa' or c=='ー')

class Voicevox:
    def __init__(self,base,speed,cache):
        self.base=base.rstrip('/');self.speed=speed;self.cache=cache;cache.mkdir(parents=True,exist_ok=True)
        self.version=json.loads(urllib.request.urlopen(self.base+'/version',timeout=10).read())
    def post(self,path,params,data=b''):
        req=urllib.request.Request(self.base+'/'+path+'?'+urllib.parse.urlencode(params),data=data,headers={'Content-Type':'application/json'})
        return urllib.request.urlopen(req,timeout=180).read()
    def query(self,text,speaker):
        key=hashlib.sha256(json.dumps([self.version,speaker,text,self.speed],ensure_ascii=False).encode()).hexdigest()
        path=self.cache/(key+'.json')
        if path.exists():q=json.loads(path.read_text())
        else:
            q=json.loads(self.post('audio_query',{'text':text,'speaker':speaker}))
            q.update(speedScale=self.speed,outputSamplingRate=RATE,outputStereo=False,prePhonemeLength=.08,postPhonemeLength=.12)
            path.write_text(json.dumps(q,ensure_ascii=False))
        return key,q
    def synthesize(self,text,speaker):
        key,q=self.query(text,speaker);path=self.cache/(key+'.wav')
        if not path.exists():
            raw=self.post('synthesis',{'speaker':speaker},json.dumps(q).encode());temp=path.with_suffix('.tmp');temp.write_bytes(raw);temp.replace(path)
        with wave.open(str(path)) as w:
            assert w.getframerate()==RATE and w.getsampwidth()==2 and w.getnchannels()==1
            count=w.getnframes();pcm=w.readframes(count)
        return pcm,count,q

def caption_bounds(line,q,duration,client,speaker):
    chunks=line.get('captions') or [{'show':line['show'],'say':line['say']}]
    if ''.join(c['show'] for c in chunks)!=line['show']:raise ValueError('Caption text differs from utterance')
    times=[q['prePhonemeLength']/q['speedScale']];counts=[0];t=times[0];count=0
    for phrase in q['accent_phrases']:
        for mora in phrase['moras']:
            t+=((mora.get('consonant_length') or 0)+mora['vowel_length'])/q['speedScale']
            count+=len(normalize(mora['text']));times.append(t);counts.append(count)
        if phrase.get('pause_mora'):
            t+=phrase['pause_mora']['vowel_length']/q['speedScale'];times[-1]=t
    total=t+q['postPhonemeLength']/q['speedScale']
    weights=[]
    for chunk in chunks:
        _,short=client.query(chunk.get('say',chunk['show']),speaker)
        weights.append(sum(len(normalize(m['text'])) for p in short['accent_phrases'] for m in p['moras']))
    bounds=[0.0];acc=0
    for weight in weights[:-1]:
        acc+=weight;target=acc/max(1,sum(weights))*count
        i=min(bisect.bisect_left(counts,target),len(times)-1)
        bounds.append(times[i]/total*duration)
    bounds.append(duration)
    for a,b in zip(bounds,bounds[1:]):
        if b-a<.02:raise ValueError('Caption boundary too short')
    return [(c['show'],a,b) for c,a,b in zip(chunks,bounds,bounds[1:])]

def generate(args):
    ep=json.loads(args.input.read_text());date=ep['date'];lang=ep.get('lang','ja')
    target=ROOT/'episodes'/f'{date}-{lang}.json'
    if target.exists() and not args.replace:raise ValueError(f'Existing episode protected: {target}')
    audio_path=ROOT/ep['audio']
    if not audio_path.resolve().is_relative_to((ROOT/'audio').resolve()):raise ValueError('Audio output must stay in audio/')
    client=Voicevox(args.engine,args.speed,args.cache)
    speakers=json.loads(urllib.request.urlopen(client.base+'/speakers',timeout=10).read())
    for speaker in ep['speakers'].values():
        matched=next(x for x in speakers if x['name']==speaker['name'])
        speaker['id']=next(x['id'] for x in matched['styles'] if x['name']=='ノーマル')
    groups=[('opening',None,ep['opening'])]+[('news',i,n['lines']) for i,n in enumerate(ep['news'])]+[('closing',None,ep['closing'])]
    ep['lines_timed']=[];ep['speech_timed']=[];ep['segments']=[]
    frames=0;total_lines=sum(len(lines) for _,_,lines in groups);line_count=0
    audio_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='tabito-voice-') as tmp:
        wav_path=Path(tmp)/'episode.wav'
        with wave.open(str(wav_path),'wb') as out:
            out.setnchannels(1);out.setsampwidth(2);out.setframerate(RATE)
            for kind,index,lines in groups:
                start=frames/RATE;part=len(ep['segments'])
                for line in lines:
                    speaker=ep['speakers'][line['speaker']]['id']
                    pcm,n,q=client.synthesize(line['say'],speaker);line_start=frames/RATE;out.writeframes(pcm);frames+=n
                    ep['speech_timed'].append({'start':round(line_start,3),'end':round(frames/RATE,3),'show':line['show'],'speaker':line['speaker'],'part':part})
                    for show,a,b in caption_bounds(line,q,n/RATE,client,speaker):
                        ep['lines_timed'].append({'start':round(line_start+a,3),'end':round(line_start+b,3),'show':show,'speaker':line['speaker'],'part':part})
                    silence=round(RATE*.16);out.writeframes(b'\0'*(silence*2));frames+=silence
                    line_count+=1
                    print(f'VOICE {line_count}/{total_lines} [{line["speaker"]}] {frames/RATE:.1f}s',flush=True)
                silence=round(RATE*.25);out.writeframes(b'\0'*(silence*2));frames+=silence
                ep['segments'].append({'kind':kind,**({'index':index} if index is not None else {}),'start':round(start,3),'end':round(frames/RATE,3),'speaker':lines[0]['speaker']})
        ep['seconds']=round(frames/RATE,3)
        encoded=audio_path.with_suffix('.tmp.m4a')
        subprocess.run(['/usr/bin/afconvert','-f','m4af','-d','aac@24000','-b','64000',str(wav_path),str(encoded)],check=True)
        if encoded.stat().st_size<1000:raise ValueError('Encoded audio is empty')
        encoded.replace(audio_path)
    target.write_text(json.dumps(ep,ensure_ascii=False,indent=2)+'\n')
    index_path=ROOT/'episodes.json';entries=json.loads(index_path.read_text())
    entry=next((x for x in entries if x['date']==date),None)
    if entry is None:entry={'date':date};entries.append(entry)
    entry[lang]={'title':ep['title'],'seconds':ep['seconds']}
    entries.sort(key=lambda x:x['date'],reverse=True);index_path.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'date':date,'seconds':ep['seconds'],'captions':len(ep['lines_timed']),'audio_bytes':audio_path.stat().st_size},ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--engine',default='http://127.0.0.1:50021');p.add_argument('--speed',type=float,default=1.07);p.add_argument('--cache',type=Path,default=Path('/private/tmp/tabito-voicevox-cache-v2'));p.add_argument('--replace',action='store_true');generate(p.parse_args())

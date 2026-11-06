"""Create short captions from existing speech, using original VOICEVOX phoneme timing (no synthesis)."""
from pathlib import Path
import json,re,urllib.request,urllib.parse,unicodedata,bisect
root=Path(__file__).resolve().parents[1];p=root/'episodes/2026-11-06-ja.json';ep=json.loads(p.read_text())
specs='''おはようございます。|11月6日、|今朝チェックした航空ニュースを|5件お届けします。
冬の新路線から、|大型の機材発注、|季節便の見直しまで。|男女のナレーションで|順番に見ていきましょう。
最初はカナダのポーター航空です。|オタワから、|冬の休暇に向けた|4つの路線を展開します。
アルバは11月7日、|モンテゴベイは|11月25日に就航予定です。
続いて、プロビデンシアレスは|12月17日、|ロスカボスは12月18日。|機材は132席の|エンブラエルE195-E2です。
2つ目は、|モルドバの新しい航空会社、|ポラリスです。|首都キシナウを拠点に、|定期便の展開を進めています。
イスタンブールに加え、|ボローニャ、ダブリン、プラハ、|ローマなどへ就航する計画です。
初期の7路線に加え、|11月から12月にかけて|計11路線を展開すると|報じられています。
運航許可の取得も報じられており、|最初の商業便には|エアバスA321を使用します。
3つ目はアメリカのブリーズ航空。|スピリット撤退後の|直行便を補う動きと、|リゾート路線の拡大です。
ラトローブから|マートルビーチへは|2027年2月9日、|オーランドへは5月26日に|就航する予定です。
タンパからは、|セントトーマスへ|今年12月16日、|モンテゴベイとカンクンへ|12月19日に就航予定。
サントドミンゴへは|来年6月18日から。|さらに、バッファロー発の|3路線も、|来年6月から7月に|順次始まる計画です。
4つ目は、|航空機リース会社アボロンの|大型発注です。
10月に公表された|合計250機の|発注パッケージのうち、|ボーイング140機は、|すべて737 MAX 10となることが|11月4日に確定発表されました。
エアバス分は、|A320neoファミリーが75機、|A330neoが35機。|さらに100機分の|追加オプションも設けています。
なお、追加オプションは、|確定発注の250機とは|別の枠です。
最後は、ユナイテッド航空の|サンフランシスコ、|アデレード線です。
運航計画に関する報道では、|2026年から27年のシーズンは、|当初の49往復から|23往復へ縮小します。
運航期間は12月17日から|翌年2月8日まで。|機材はボーイング787-9です。
季節便を利用する方は、|旅行日程に合う便があるか、|予約前に最新の運航予定を|確認したいところです。
今朝の航空ニュースは、|新路線の拡大、大型発注、|そして季節便の見直しを|お伝えしました。
詳しい日程と出典は、|画面下の各ニュースから|確認できます。|運航予定は変更される場合が|あります。|それでは、また次の放送で。'''.splitlines()
original=ep.get('speech_timed',ep['lines_timed']);ep['speech_timed']=original
spoken=ep['opening']+[l for n in ep['news'] for l in n['lines']]+ep['closing']
assert len(specs)==len(original)==len(spoken)
def query(text,speaker):
 u='http://127.0.0.1:50021/audio_query?'+urllib.parse.urlencode({'text':text,'speaker':speaker})
 return json.loads(urllib.request.urlopen(urllib.request.Request(u,data=b''),timeout=30).read())
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if '\u30a1'<=c<='\u30fa' or c=='ー')
def say(s):
 for a,b in [('E195-E2','イーいちきゅうご、イーツー'),('A321','エーさんにいいち'),('737 MAX 10','ななさんなな、マックステン'),('A320neo','エーさんにいまるネオ、'),('A330neo','エーさんさんまるネオ'),('787-9','ななはちなな、ダッシュナイン')]:s=s.replace(a,b)
 return s
rows=[]
for old,sp,spec in zip(original,spoken,specs):
 chunks=spec.split('|');assert ''.join(chunks)==old['show'],old['show']
 speaker=ep['speakers'][old['speaker']]['id'];q=query(sp['say'],speaker)
 # The exact full-utterance query supplies timing. Short queries supply reading lengths.
 times=[0.08];counts=[0];t=.08;count=0
 for phrase in q['accent_phrases']:
  for mora in phrase['moras']:
   t+=(mora.get('consonant_length') or 0)+mora['vowel_length'];count+=len(norm(mora['text']));times.append(t);counts.append(count)
  if phrase.get('pause_mora'):t+=phrase['pause_mora']['vowel_length'];times[-1]=t
 t+=.12
 weights=[sum(len(norm(m['text'])) for a in query(say(c),speaker)['accent_phrases'] for m in a['moras']) for c in chunks]
 total=sum(weights);acc=0;bounds=[old['start']]
 for w in weights[:-1]:
  acc+=w;target=acc/total*count;i=min(bisect.bisect_left(counts,target),len(times)-1)
  bounds.append(round(old['start']+(old['end']-old['start'])*times[i]/t,3))
 bounds.append(old['end'])
 for i,c in enumerate(chunks):rows.append({**old,'show':c,'start':bounds[i],'end':bounds[i+1]})
print('Captions:',len(original),'->',len(rows));ep['lines_timed']=rows
p.write_text(json.dumps(ep,ensure_ascii=False,indent=2))

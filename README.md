# ニュースラジオ（仮称）

航空ニュースを男女のナレーションで届けるWeb番組です。

[番組を聴く](https://kumokazetabito.github.io/myradio/#aviation/2026-11-06/ja) / [11月6日の記事を読む](docs/aviation-2026-11-06.md)

## 11月6日の5件
- ポーター：オタワから南国へ4路線
- ポラリス：モルドバ発の路線展開
- ブリーズ：米国内・カリブ海方面の拡大
- アボロン：250機の発注パッケージ
- ユナイテッド：アデレード季節便の縮小

音声はVOICEVOX:四国めたん（1・3・5件）／VOICEVOX:玄野武宏（2・4件）。各記事に出典、字幕、補足を掲載しています。番組は約2分50秒です。

## 素材とライセンス
画面の元ソース：[monoradio102/myradio](https://github.com/monoradio102/myradio)。プログラムはMIT（LICENSE参照）。女性キャラは元作者がREADMEで許諾した範囲で利用。男性キャラはこの番組用のAI生成画像です。画像と音声の公式キャラクターは別です。男性は音声連動の口（閉じ・半開き・開き）と自然なまばたきに対応しています。

[VOICEVOX](https://voicevox.hiroshiba.jp/term/)／[四国めたん音源規約](https://www.zunko.jp/con_ongen_kiyaku.html)／[玄野武宏音源規約](https://www.virvoxproject.com/voicevoxの利用規約)

## 配信
mainはソースと台本。音声はmainに保存せず、公開用gh-pagesにのみ配置します。設定はstation.json、番組はepisodes/とepisodes.jsonを参照します。

## 番組URL

航空ニュースは `#aviation/YYYY-MM-DD/ja`。以前の `#YYYY-MM-DD/ja` も開け、正規URLへ切り替わります。番組IDはstation.jsonのprogram.idで設定します。他ジャンルの番組一覧・切り替え画面は今後の拡張です。

# Tabito Radio

航空ニュースを男女のナレーションで届けるWeb番組です。

[番組を聴く](https://kumokazetabito.github.io/myradio/aviation/2026-11-06/ja/) / [11月6日の記事を読む](docs/aviation-2026-11-06.md)

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

## 番組URLと検索・SNS対応

正規URLは `/myradio/aviation/YYYY-MM-DD/ja/`。各URLに実際のHTMLがあり、直接アクセス・再読み込みが可能です。記事・台本・出典はJavaScriptを実行しなくてもHTML内にあります。音声プレーヤーとキャラは同じページで動作します。

従来の `#aviation/YYYY-MM-DD/ja` と `#YYYY-MM-DD/ja` も開け、正規URLへ切り替わります。共有・埋め込み・過去の放送一覧も正規URLを使用します。他ジャンルの番組切り替えは今後の拡張です。

各放送回に専用のtitle、description、canonical、Open Graph、Twitterカード、構造化データ、1200×630のPNG画像を生成します。`sitemap.xml` も更新します。画像用フォントはビルド時のみ使用し、ブラウザーでは読み込みません。検索結果への掲載やSNSサービス側のキャッシュ更新は、このビルドだけで即時に保証されるものではありません。

### 更新手順

画面を修正する場合は **`templates/player.html`** を編集します。ルートの `index.html` と各放送回のHTMLは生成物です。直接編集しないでください。

```sh
python3 -m venv .venv-pages
.venv-pages/bin/python -m pip install -r tools/requirements-pages.txt
# 台本・音声・一覧を更新後、公開済み放送回のページをまとめて生成
.venv-pages/bin/python tools/build_pages.py
.venv-pages/bin/python -m unittest discover -s tests -v
node tests/test_routes.cjs
# mainにソースと生成物をコミット・pushした後
PAGES_PYTHON=.venv-pages/bin/python tools/publish.sh
```

`.venv-pages/` と音声はmainに入れません。`tools/publish.sh` は既存のgh-pages worktreeを使い、force push・履歴リセット・古い音声の自動削除を行いません。`PAGES_WORKTREE` でworktreeの場所を指定できます。既定値はリポジトリの隣の `github-radio-publish` です。公開前に、そのworktreeに未保存の変更がないことを確認します。

新しい台本ツールからは、完成した `episodes/*.json` と `episodes.json`、音声を出力後、`tools/build_pages.py` を呼び出してください。`pages-manifest.json` に生成した公開ファイル一覧があります。

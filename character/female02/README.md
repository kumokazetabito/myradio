# female02 — 猫の女性キャラクター

AI生成。採用された基準画像を変更せず、顔の差分だけを重ねる既存プレーヤー互換のスプライト素材。

- base.png：口を閉じ、両目を開いた基準画像（1199×1312、透過PNG）
- mouth_half.png / mouth_open.png：音声連動の口差分
- half_blink.png / blink.png：まばたき途中・閉じ目の差分
- depth.png：頭・顔・胴体・後ろ髪の奥行きを表す動作用画像
- character.json：差分の位置・動作設定

差分画像は独立した顔全体の画像ではなく、小さい透過パッチ。必ずcharacter.jsonのx/yでbase.pngに重ねて使用する。
既存のプレーヤーが音声の大きさに応じて口を開閉し、まばたき、呼吸、顔・上半身の向き、後ろ髪の揺れを行う。目・口も本体と一緒に変形する。

奥行き画像は `tools/build_female02_depth.py` で基準画像と同じ1199×1312に再生成できる。基準画像・採用済みの目と口の差分は変更しない。

配信画面で選択する際は、局またはチャンネルのcharacter.packをcharacter/female02/character.json、thumbnailをcharacter/female02/base.pngに設定する。

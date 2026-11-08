# male02 — ライオンの男性キャラクター

AI生成。経済ニュース(SIN)用。黄褐色のたてがみの採用画像をそのまま基準に使用。

- base.png：目を開き口を閉じた基準画像（1199×1312、背景透過）
- mouth_half.png / mouth_open.png：音声に合わせる口の半開き・開き
- half_blink.png / blink.png：まばたき途中・閉じ目
- depth.png：呼吸・顔と上半身の向き・たてがみの揺れに使う奥行きデータ
- character.json：配置座標、目・口と奥行きの設定

目と口は小さい透過画像。character.jsonの座標に重ねて使う。元の髪・衣装・体を差分で置き換えない。
体は別ポーズの画像切替ではなく、奥行きを使った連続変形。目・口も同じ変形に追従する。
奥行きデータは `tools/build_male02_depth.py` で再生成できる。
航空ニュースのmale01は維持し、経済ニュースのcharacter.male_packだけをmale02に設定する。

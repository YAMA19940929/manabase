# 小判が外国へ流れ出た話(幕末の金流出・小6社会・約72秒)

- `kin_ryushutsu_short.mp4`: 公開用の動画(縦1080×1920、AivisSpeech「阿井田 茂」のナレーションと字幕入り)
- `kin_ryushutsu_short.srt`: 字幕ファイル
- `build.py`: 台本からスライド・音声・動画を作るスクリプト(台本は `SCRIPT` に書いてある)

## 版の記録

- **第1版(2026-11-22):** `CLAUDE.md` の5つの手順(/teacher → /yt-script → 阿井田 茂の声 → /factcheck・/critique → 公開)で作成。
  - 冒頭は hookscore 54点(The Question)。もう1案は42点。
  - /factcheck:13件すべて資料と一致。流出した量は研究者によって1万両〜2,000万両と大きく違うので、数字は入れていない。
    日本側の金銀比率も資料によって 1:5〜1:10 程度と幅があるので、「日本は外国より金がずっと安かった」とだけ言う。
  - /critique:字幕14枚すべて目安内。

## YouTube に載せるときの文章

タイトル:

    両替だけで3倍？幕末に小判が消えた理由【小6社会】

説明欄:

    両替するだけで、お金が3倍。そんなことが、開国したばかりの日本で本当に起きていました。

    ・1859年、横浜などの港が開いて外国との貿易が始まった
    ・外国の銀貨(洋銀)1枚は、日本の一分銀3枚と交換できた。一分銀4枚で小判1枚
    ・日本は外国より金が安かったので、小判を外国に持ち出して銀に替えると、およそ3倍になった
    ・1860年、幕府は金を約3分の1に減らした「万延小判」を作って流出を止めたが、物の値段が大きく上がった

    #江戸時代 #幕末 #開国 #小6社会 #社会科 #Shorts

    音声:AivisSpeech(阿井田 茂)

タグ: 幕末, 開国, 小判, 金の流出, 万延小判, 一分銀, 小6 社会, 歴史 小学生

公開先チャンネル: Teacher YAMA。「子ども向け」の設定は、公開前にオーナーが決める。

## 参考にした資料

- 財務省『大蔵省史』第1期 第4章 https://www.mof.go.jp/pri/publication/mof_history/1ki_c4.pdf
- Cambridge "Ryogae: struggling for survival, 1859–1868"
  https://cambridge.org/core/books/japanese-banking/ryogae-struggling-for-survival-18591868/D0E6A7AD5775E3B38B0C23B442455F06
- 東北学院大学 高橋秀悦 論文 https://tohoku-gakuin.repo.nii.ac.jp/record/24155/files/20200305_15_takahashishuetsu.pdf
- 野村證券「金貨の改鋳」 https://www.nomura.co.jp/fin-wing/column/goldcoin-recoinage/

## 作り直すとき

    bash tools/voice/aivis_up.sh   # 声(AivisSpeech 阿井田 茂)。Docker が必要
    apt-get install -y fonts-noto-cjk ffmpeg
    python3 build.py   # スライドと音声を作り、MP4 と SRT まで書き出す(途中のファイルは build/ に入る)

読み上げ用の文では、数字・年号・硬貨の名前(一分銀、洋銀、万延小判)をひらがなで書いている。
AivisSpeech は読み仮名を返さないので、読み間違いを防ぐため。

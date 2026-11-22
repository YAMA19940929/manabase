# 参勤交代ショート(小6社会・約53秒)

- `sankin_kotai_short.mp4`: 公開用の動画(縦1080×1920、VOICEVOX:玄野武宏 のナレーションと字幕入り)
- `sankin_kotai_short.srt`: 字幕ファイル
- `build.py`: 台本からスライド・音声・動画を作るスクリプト(台本は `SCRIPT` に書いてある)

## YouTube に載せるときの文章

タイトル:

    参勤交代、なぜ大名は従ったの？【小6社会】

説明欄:

    1年おきに家族と離れて江戸へ。お金は全部自分もち。
    それでも大名が参勤交代に従ったのは、幕府のねらいがまさに「お金」だったから。
    でもその行列のおかげで、日本中がつながっていったんだ。

    ・1635年、3代将軍 徳川家光のころに決まりになった
    ・大名は1年ごとに領地と江戸を行ったり来たり
    ・奥さんと子どもは江戸に住みっぱなし
    ・行列の費用はぜんぶ大名もち

    #参勤交代 #小6社会 #江戸時代 #社会科 #Shorts

    音声:VOICEVOX:玄野武宏

タグ: 参勤交代, 小6 社会, 江戸時代, 徳川家光, 大名, 歴史 小学生

公開先チャンネル: Teacher YAMA。「子ども向け」の設定は、公開前にオーナーが決める。

## 作り直すとき

    docker run -d -p 127.0.0.1:50021:50021 voicevox/voicevox_engine:cpu-latest   # 声(VOICEVOX)
    apt-get install -y fonts-noto-cjk ffmpeg
    # VOICEVOX が動いていないときは Open JTalk で読む:
    # apt-get install -y open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001
    python3 build.py   # スライドと音声を作り、MP4 と SRT まで書き出す(途中のファイルは build/ に入る)

台本を変えるときは `build.py` の `SCRIPT` を直す。1行が `(画面, 字幕, 読み上げ用の文)` で、読み上げ用の文は
Open JTalk が読み間違えないように一部をかなにしてある。書き方はリポジトリ直下の `CLAUDE.md` に従う。

声は `VOICEVOX_SPEAKER` で変えられる(既定は 11 = 玄野武宏 ノーマル)。VOICEVOX の音声を使うときは、説明欄に
「VOICEVOX:キャラクター名」のクレジットを入れる。キャラクターごとの利用規約も守る。

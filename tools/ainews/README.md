# AIニュースのまとめ動画(のらぬっこ・毎日)

note のAIニュース記事(ChatGPTの添削とClaudeの校正が済んだもの)を、その日の分まとめて1本の縦長動画にする。
公開先は YouTube の「のらぬっこ」。Teacher YAMA には出さない(教育系の動画だけにするため)。

## 毎日の流れ

1. **材料を選ぶ。** Jetpost で、タイトルが「AIニュース記事の下書き」で始まるノートのうち、次の両方を満たす一番新しいもの。
   - Claude の「校正が完了しました」のコメントがある(ChatGPT の添削を反映したあとの版)。
   - 「動画準備完了」のコメントがまだない。
   なければ何もしないで終わる。
2. **台本(`content/ainews/<日付>/script.json`)を書く。** 形は `digest.py` の説明どおり。
   - 記事の本文にある事実・数字・固有名詞だけを使う。新しい事実を足さない。記事の「まだ分からないこと」を言い切りにしない。
   - 1本あたり2〜3文。全体で3分以内(`digest.py` が178秒を超えたら止まる)。
   - 書き方はリポジトリ直下の `CLAUDE.md` に従う(話し言葉、決まり文句なし、まとめで終わらない、素直な感想を1〜2か所)。
     毎日同じ言い回しにならないよう、冒頭の一言と、本と本のつなぎ方を日ごとに変える。
   - 字幕は1行16字・2行まで。読み上げ用の文は、数字・年号・英語の社名・人名をかなにする。
   - Anthropic・Claude が出てくるニュースでは、台本づくりに Claude を使っていることを、動画と説明欄で示す。
   - 株価などのニュースでは、説明欄に「投資の勧誘や助言ではありません」を入れる。
3. **動画を作る。**
   ```bash
   bash tools/voice/aivis_up.sh            # 声(AivisSpeech 阿井田 茂)。先に dockerd をバックグラウンドで起動しておく
   python3 tools/ainews/digest.py content/ainews/<日付>/script.json
   ```
   字幕がはみ出すと `digest.py` が止まって教えてくれるので、直して作り直す。
4. **点検する。** `python3 .claude/skills/critique/subcheck.py content/ainews/<日付>/ainews_<日付>.srt`、
   `python3 .claude/skills/yt-package/title.py --title "<タイトル>"`。台本の事実が記事と食い違っていないかも読み直す。
5. **Jetpost で渡す。** `upload_media` で MP4 を上げ、「AIニュース動画 <日付>版(のらぬっこ・アップロード準備完了)」の
   ノートを作る(動画、アップロードの手順、`youtube.md` のタイトル・説明欄・タグ、台本と点検の結果)。
   そのノートに `add_comment`(notify: true)でオーナーに知らせ、材料の下書きノートに「動画準備完了」と書く。
6. **アップロードと公開はオーナーがする。** Claude は YouTube にアップロードも公開もしない。

## ファイル

- `digest.py` … 台本 JSON から MP4・SRT・`youtube.md` を作る
- `content/ainews/<日付>/script.json` … その日の台本(リポジトリに残す)。MP4 と build/ は残さない(Jetpost で渡す)

---
name: critique
description: >-
  Review a Teacher YAMA script or finished Short before publishing, through the
  eyes of a 6th grader, a parent and a fellow teacher, and name the ONE thing to
  fix first. Use for "/critique", "公開前に見て", "弱点を教えて", "これで大丈夫？",
  or any request to check a script, subtitles or video before it goes out.
---

# critique

公開前の最後の点検。気になるところを20個並べるのではなく、**いちばん先に直すことを1つ**に絞る。

## 見るもの

手元にあるものを全部使う:台本、字幕(.srt)、`build.py`、タイトル・説明欄、動画。

## 手順

1. **道具で測れるものを先に測る。**

   ```bash
   python3 subcheck.py <字幕.srt>                                   # 字幕の速さと長さ
   python3 ../yt-script/hookscore.py --hook "<冒頭の一文>"            # 冒頭の強さ
   python3 ../yt-package/title.py --title "<タイトル>" --thumb "<サムネの文字>"
   python3 ../factcheck/claims.py <台本 | 字幕 | build.py>          # 確かめるべき文
   ```

   `subcheck.py` の目安(1秒に6文字、1行16文字)は、このリポジトリの縦長ショート向けに決めたもので、公式の基準ではない。

2. **3人の目で見る。**
   - **小6の子**:最初の3秒で続きを見たくなるか。知らない言葉がないか。字幕を読み切れるか。最後に何か1つ残るか。
   - **保護者**:内容は正しいか。子どもに見せて困る表現はないか。広告や外部への誘導が入っていないか。
   - **同僚の先生**:教科書の内容とずれていないか。言い切りすぎの解釈がないか(`/factcheck` の「解釈」)。

3. **書き方のルールを見る。** `CLAUDE.md` の「使わない言葉」「入り方と終わり方」に当てはまるところがないか。

4. **公開の設定を見る。** 「子ども向け」の設定を選んだか、説明欄に VOICEVOX などのクレジットがあるか、タイトルがスマホで切れても意味が通じるか。

## 返すもの

- **まず直すこと(1つ)**:何を、どう直すか。理由を一言。
- **ほかに気になること**:3つまで。重要な順。
- **よかったところ**:2つ。直すときに壊さないように、具体的に書く。
- 道具の結果は、問題があった行だけを短く載せる。

最後の1行は「このまま出す？それとも直す？」。

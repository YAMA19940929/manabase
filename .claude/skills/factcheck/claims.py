#!/usr/bin/env python3
"""claims.py - 台本や教材から「確かめるべき文」を抜き出す。

    python3 claims.py script.txt          # テキスト / Markdown
    python3 claims.py subtitles.srt       # 字幕ファイル
    python3 claims.py build.py            # content/shorts/*/build.py の SCRIPT(読み上げ文)
    python3 claims.py --json script.txt

文ごとに、確かめる理由をタグで付ける。
  [年号]  1635年、江戸時代、寛永 など時代や年
  [数字]  何百人、3代、45秒 など数や量
  [名前]  漢字やカタカナの固有名詞らしい語(徳川家光、武家諸法度 など)。人名・制度名・地名の候補
  [因果]  「〜ため」「〜から」「ねらい」「理由」など、原因や目的を言い切っている文。解釈が分かれやすい
  [断定]  「必ず」「いちばん」「だけ」「全部」など、言い切りが強い文

これは機械的な抜き出しで、正しいかどうかは判定しない。判定は /factcheck の手順で行う。
"""
import ast, json, os, re, sys

ERA = r"(縄文|弥生|古墳|飛鳥|奈良|平安|鎌倉|室町|戦国|安土桃山|江戸|明治|大正|昭和|平成|令和|寛永|元禄|享保|天保)"
TAGS = [
    ("年号", re.compile(r"[0-9０-９]{3,4}\s?年|" + ERA + r"(時代)?")),
    ("数字", re.compile(r"[0-9０-９]+|[一二三四五六七八九十百千万]+(人|代|年|回|つ|か所|か国|倍|割)|何(百|千|万)")),
    ("名前", re.compile(r"[一-鿿々]{3,}|[ァ-ヺ][ァ-ーー]{2,}")),
    ("因果", re.compile(r"ため|から[、。]|ので|ねらい|狙い|理由|目的|おかげ|せいで|によって|結果")),
    ("断定", re.compile(r"必ず|絶対|いちばん|一番|最も|だけ|しかない|全部|ぜんぶ|すべて|唯一|はじめて|初めて")),
]

def sentences_from(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    if path.endswith(".py"):
        m = re.search(r"SCRIPT\s*=\s*(\[.*?\n\])", raw, re.S)
        if not m: sys.exit("no SCRIPT list found in " + path)
        rows = ast.literal_eval(m.group(1))
        text = "\n".join(r[2] if len(r) > 2 else r[1] for r in rows)
    elif path.endswith(".srt") or path.endswith(".vtt"):
        text = "\n".join(l for l in raw.splitlines()
                         if l.strip() and not l.strip().isdigit() and "-->" not in l and l.strip() != "WEBVTT")
    else:
        text = raw
    parts = re.split(r"(?<=[。！？!?])|\n", text)
    out, seen = [], set()
    for p in parts:
        p = p.strip(" \t　…・-#*>|")
        if len(p) < 4 or p in seen: continue
        seen.add(p); out.append(p)
    return out

def main():
    a = sys.argv[1:]
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    if not a or not os.path.exists(a[0]): print(__doc__); sys.exit(1)
    rows = []
    for s in sentences_from(a[0]):
        tags = [name for name, rx in TAGS if rx.search(s)]
        # 「名前」だけで他のタグがない短い文は、ふつうの言葉のことが多いので外す
        if not tags or (tags == ["名前"] and len(s) < 12): continue
        rows.append({"text": s, "tags": tags})
    if as_json: print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    print(f"\n  {a[0]}: 確かめる候補 {len(rows)} 件\n")
    for i, r in enumerate(rows, 1):
        print(f"  {i:2d}. [{'・'.join(r['tags'])}] {r['text']}")
    print("\n  機械的な抜き出しです。正しいかどうかは /factcheck の手順で一つずつ確かめてください。\n")

if __name__ == "__main__":
    main()

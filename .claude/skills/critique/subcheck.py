#!/usr/bin/env python3
"""subcheck.py - 字幕(SRT)が読み切れる速さ・長さになっているかを調べる。

    python3 subcheck.py subtitles.srt
    python3 subcheck.py subtitles.srt --cps 6 --line 16 --json

字幕1枚ごとに、表示時間と文字数(句読点・記号・空白を除く)から「1秒あたりの文字数」を出し、
次のどれかに当てはまるものを挙げる。
  FAST   1秒あたりの文字数が --cps を超える(読み切れないおそれ)
  LONG   1行の文字数が --line を超える(縦長画面で横にはみ出すおそれ)
  LINES  3行以上ある
  SHORT  表示が1秒未満

--cps の初期値 6、--line の初期値 16 は、このリポジトリの縦長ショート(字幕58pxで幅900px)に合わせた
目安で、公式の基準ではない。見る人の年齢や画面に合わせて変えてよい。
"""
import json, os, re, sys

def ts(s):
    h, m, rest = s.strip().replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)

def load(path):
    cues, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace").read().splitlines():
        m = re.match(r"\s*([\d:,.]+)\s*-->\s*([\d:,.]+)", line)
        if m:
            cur = {"start": ts(m.group(1)), "end": ts(m.group(2)), "lines": []}; cues.append(cur)
        elif cur is not None and line.strip() and not line.strip().isdigit():
            cur["lines"].append(line.strip())
        elif not line.strip():
            cur = None
    return [c for c in cues if c["lines"]]

def count(t): return len(re.sub(r"[\s、。,.!?！？「」『』…・ー〜~()（）]", "", t))

def main():
    a = sys.argv[1:]
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    cps_max = float(a[a.index("--cps") + 1]) if "--cps" in a else 6.0
    line_max = int(a[a.index("--line") + 1]) if "--line" in a else 16
    files = [x for x in a if x.endswith((".srt", ".vtt"))]
    if not files or not os.path.exists(files[0]): print(__doc__); sys.exit(1)
    rows = []
    for i, c in enumerate(load(files[0]), 1):
        dur = max(0.001, c["end"] - c["start"])
        n = sum(count(l) for l in c["lines"])
        flags = []
        if n / dur > cps_max: flags.append("FAST")
        if any(len(l) > line_max for l in c["lines"]): flags.append("LONG")
        if len(c["lines"]) > 2: flags.append("LINES")
        if dur < 1.0: flags.append("SHORT")
        rows.append({"cue": i, "start": round(c["start"], 2), "seconds": round(dur, 2), "chars": n,
                     "cps": round(n / dur, 1), "flags": flags, "text": " / ".join(c["lines"])})
    if as_json: print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    bad = [r for r in rows if r["flags"]]
    print(f"\n  {files[0]}: 字幕 {len(rows)} 枚、気になるもの {len(bad)} 枚(目安 {cps_max}字/秒・1行{line_max}字)\n")
    for r in rows:
        mark = ",".join(r["flags"]) or "ok"
        print(f"  {r['cue']:2d} {r['start']:6.1f}s {r['seconds']:4.1f}s {r['chars']:3d}字 {r['cps']:4.1f}字/秒  {mark:<10} {r['text']}")
    print()

if __name__ == "__main__":
    main()

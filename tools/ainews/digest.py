#!/usr/bin/env python3
"""digest.py - その日のAIニュースを1本のまとめ動画にする(のらぬっこ・形B)。

    python3 tools/ainews/digest.py content/ainews/2026-11-21/script.json

script.json(台本)から、同じフォルダに次を作る:
  ainews_<日付>.mp4   縦1080×1920、3分以内(YouTube ショートの上限)
  ainews_<日付>.srt   字幕
  youtube.md          YouTube に貼るタイトル・説明欄・タグ
途中のファイルは build/ に入る。

script.json の形:
{
  "date": "2026-11-21",
  "title": "YouTube のタイトル",
  "intro": [["字幕", "読み上げ"], ...],
  "items": [
    {"label": "画面に出す短い見出し", "lines": [["字幕", "読み上げ"], ...],
     "sources": [["出典名", "URL"], ...]}
  ],
  "outro": [["字幕", "読み上げ"], ...],
  "description_lead": "説明欄の最初の1〜2文",
  "notes": ["説明欄の最後に入れる注記(開示・投資助言でない など)"],
  "tags": ["タグ", ...]
}

字幕は1行16字・2行まで、読み上げ用の文は数字や英語の社名をかなにしておく(AivisSpeech は読み仮名を返さない)。
声は tools/voice/tts.py(AivisSpeech 阿井田 茂)。台本の書き方はリポジトリ直下の CLAUDE.md に従う。
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "voice"))
from tts import synthesize  # noqa: E402

W, H = 1080, 1920
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BG, INK, ACCENT, SUB, CARD, LINE = (17, 22, 33), (240, 242, 246), (255, 179, 64), (150, 160, 178), (31, 38, 54), (64, 74, 96)
CHANNEL = "のらぬっこ"
MAX_SECONDS = 178          # stay under YouTube's 3-minute Shorts limit
SUB_MAX_W = 900            # subtitle box inner width at 58px

def font(p, s): return ImageFont.truetype(p, s)

def center(d, xy, text, f, fill, spacing=16):
    d.multiline_text(xy, text, font=f, fill=fill, anchor="mm", align="center", spacing=spacing)

def wrap(text, f, width, d):
    """Keep the label's own line breaks; break further only where a line is still too wide."""
    out = []
    for part in text.split("\n"):
        cur = ""
        for ch in part:
            if d.textlength(cur + ch, font=f) > width and cur:
                out.append(cur); cur = ch
            else:
                cur += ch
        out.append(cur)
    return "\n".join(out)

def fit_one_line(text, f, width, d):
    text = text.replace("\n", "")
    if d.textlength(text, font=f) <= width: return text
    while text and d.textlength(text + "…", font=f) > width: text = text[:-1]
    return text + "…"

def check_subtitles(spec):
    d = ImageDraw.Draw(Image.new("RGB", (9, 9)))
    f = font(BOLD, 58)
    bad = []
    for sub, _ in all_lines(spec):
        rows = sub.split("\n")
        if len(rows) > 2: bad.append(f"3行以上: {sub!r}")
        for r in rows:
            if d.textlength(r, font=f) > SUB_MAX_W: bad.append(f"幅オーバー: {r!r}")
    if bad:
        raise SystemExit("字幕を直してください:\n  " + "\n  ".join(bad))

def all_lines(spec):
    for l in spec["intro"]: yield l
    for it in spec["items"]:
        for l in it["lines"]: yield l
    for l in spec["outro"]: yield l

def slide(spec, kind, n, sub, label, progress, path):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    m, dd = spec["date"][5:7].lstrip("0"), spec["date"][8:10].lstrip("0")
    d.rectangle([0, 0, W, 230], fill=CARD)
    center(d, (W // 2, 92), f"AIニュース {m}/{dd}", font(BOLD, 76), INK)
    center(d, (W // 2, 178), CHANNEL, font(REG, 40), ACCENT)
    total = len(spec["items"])
    if kind == "item":
        d.rounded_rectangle([W // 2 - 120, 330, W // 2 + 120, 450], radius=60, fill=ACCENT)
        center(d, (W // 2, 390), f"{n} / {total}", font(BOLD, 64), BG)
        f = font(BOLD, 84)
        center(d, (W // 2, 720), wrap(label, f, 900, d), f, INK, 22)
    elif kind == "intro":
        center(d, (W // 2, 470), f"{total}本", font(BOLD, 200), ACCENT)
        f = font(BOLD, 52)
        for k, it in enumerate(spec["items"]):
            d.text((110, 650 + k * 82), f"{k + 1}. " + fit_one_line(it["label"], f, 800, d), font=f, fill=INK)
    else:  # outro
        center(d, (W // 2, 620), "出典は概要欄に", font(BOLD, 84), INK)
        center(d, (W // 2, 760), f"{m}/{dd} のAIニュース", font(BOLD, 60), SUB)
    d.rounded_rectangle([60, 1110, W - 60, 1420], radius=36, fill=CARD, outline=LINE, width=4)
    center(d, (W // 2, 1265), sub, font(BOLD, 58), INK, 22)
    d.rectangle([0, H - 22, W, H], fill=LINE)
    d.rectangle([0, H - 22, int(W * progress), H], fill=ACCENT)
    im.save(path)

def build(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    check_subtitles(spec)
    out = os.path.dirname(os.path.abspath(spec_path))
    os.makedirs(f"{out}/build", exist_ok=True)
    seq = [("intro", 0, s, r, "") for s, r in spec["intro"]]
    for n, it in enumerate(spec["items"], 1):
        seq += [("item", n, s, r, it["label"]) for s, r in it["lines"]]
    seq += [("outro", 0, s, r, "") for s, r in spec["outro"]]
    lines, t = [], 0.0
    for i, (kind, n, sub, read, label) in enumerate(seq):
        wav, png = f"{out}/build/{i:02d}.wav", f"{out}/build/{i:02d}.png"
        dur = synthesize(read, wav) + 0.15
        slide(spec, kind, n, sub, label, (i + 1) / len(seq), png)
        lines.append({"png": png, "wav": wav, "start": t, "dur": dur, "sub": sub})
        t += dur
    lines[-1]["dur"] += 0.8; t += 0.8
    if t > MAX_SECONDS:
        raise SystemExit(f"{t:.0f}秒あります。{MAX_SECONDS}秒以内になるよう台本を短くしてください。")
    name = f"ainews_{spec['date']}"
    render(lines, out, name)
    write_youtube_md(spec, out, t)
    print(f"{len(lines)} lines, {t:.1f}s -> {out}/{name}.mp4")

def render(lines, out, name):
    segs = []
    for i, l in enumerate(lines):
        seg = f"{out}/build/seg{i:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", l["png"],
            "-i", l["wav"], "-af", "apad,aresample=48000", "-t", f"{l['dur']:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "160k", "-ac", "2", seg], check=True)
        segs.append(seg)
    with open(f"{out}/build/list.txt", "w") as f:
        f.write("".join(f"file '{os.path.basename(s)}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{out}/build/list.txt",
        "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", f"{out}/{name}.mp4"], check=True)
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
    with open(f"{out}/{name}.srt", "w", encoding="utf-8") as f:
        for i, l in enumerate(lines, 1):
            f.write(f"{i}\n{ts(l['start'])} --> {ts(l['start'] + l['dur'] - 0.15)}\n{l['sub']}\n\n")

def write_youtube_md(spec, out, seconds):
    m, dd = spec["date"][5:7].lstrip("0"), spec["date"][8:10].lstrip("0")
    desc = [spec["description_lead"], ""]
    for n, it in enumerate(spec["items"], 1):
        desc.append(f"{n}. {it['label'].replace(chr(10), ' ')}")
        for name, url in it["sources"]:
            desc.append(f"   出典:{name} {url}")
    desc += [""] + spec.get("notes", []) + ["", "#AIニュース #生成AI #Shorts", "", "音声:AivisSpeech(阿井田 茂)"]
    md = ["# YouTube に貼る文章", "", f"長さ:{seconds:.0f}秒(縦長・ショート)", "",
          "## タイトル", "", "    " + spec["title"], "",
          "## 説明欄", ""] + ["    " + l for l in desc] + ["",
          "## タグ", "", "    " + ", ".join(spec["tags"]), "",
          "## 公開の前に", "",
          "- 「子ども向け」は「いいえ」(大人向けのニュース)。",
          "- 公開範囲を選んで公開するのはオーナー。"]
    open(f"{out}/youtube.md", "w", encoding="utf-8").write("\n".join(md) + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 2: print(__doc__); sys.exit(1)
    build(sys.argv[1])

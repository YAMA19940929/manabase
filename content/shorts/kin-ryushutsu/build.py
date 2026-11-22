#!/usr/bin/env python3
"""Build a 9:16 YouTube Short for 6th graders: why Japan's gold koban flowed abroad after 1859.

Each subtitle line is voiced separately (tools/voice/tts.py), so every slide lasts exactly as long as
its narration. Slides are drawn with Pillow, then ffmpeg joins slides + audio into an MP4.
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
NAME = "kin_ryushutsu_short"
W, H = 1080, 1920
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
TITLE, GRADE = "小判が外国へ！？", "小6社会"

PAPER, INK, RED, GOLD, SOFT = (246, 239, 224), (34, 42, 74), (196, 58, 40), (214, 160, 52), (226, 214, 190)
SILVER, SILVER_DK, GOLD_DK = (205, 208, 214), (120, 124, 134), (150, 105, 25)

# (scene, subtitle shown on screen, text read aloud). The reading text spells numbers, years and
# coin names in kana, because AivisSpeech returns no reading to check and may misread them.
SCRIPT = [
    ("hook",    "もしキミが両替するだけで\nおこづかいが3倍になったら？", "もしキミが、両替するだけで、おこづかいがさんばいになるとしたら、どうする？"),
    ("bakumatsu", "これ、幕末の日本で\n本当に起きてたんだ", "これ、幕末の日本で、本当に起きてたんだ。"),
    ("port",    "1859年、日本は港を開いて\n外国と貿易を始めた", "せんはっぴゃくごじゅうきゅうねん、日本は港を開いて、外国と貿易を始めた。"),
    ("rate1",   "外国の銀貨「洋銀」1枚は\n日本の一分銀3枚と交換", "外国の銀貨、ようぎんいちまいは、日本のいちぶぎんさんまいと交換できた。"),
    ("rate2",   "で、一分銀4枚で\n小判1枚になる", "で、いちぶぎんよんまいで、小判いちまいになる。"),
    ("cheap",   "ポイントは、日本は外国より\n金がずっと安かったこと", "ポイントは、日本は外国より、金がずっと安かったってこと。"),
    ("chain",   "洋銀4枚→一分銀12枚→小判3枚\n外国で銀に替えると……", "ようぎんよんまいを、いちぶぎんじゅうにまいに。それを小判さんまいに。その小判を、外国で銀に替えると……"),
    ("triple",  "洋銀12枚分！\n両替しただけで3倍", "ようぎんじゅうにまい分くらいになる。ただ両替しただけで、さんばい。"),
    ("rule",    "ずるい？でもこれ\n条約どおりの正式な両替", "ずるいって思うよね。でもこれ、条約で決めたとおりの、正式な両替なんだよね。"),
    ("outflow", "こうして日本の小判が\nどんどん外国へ", "こうして、日本の小判が、どんどん外国へ流れ出ていった。"),
    ("fix",     "1860年、金を約3分の1に\n減らした「万延小判」", "せんはっぴゃくろくじゅうねん、幕府は、金の量を、さんぶんのいちくらいに減らした、まんえんこばんを作った。"),
    ("price",   "流出は止まった。でも……\n物の値段がぐんと上がった", "これで流出は止まった。でもそのかわり、物の値段が、ぐんと上がっちゃったんだ。"),
    ("close",   "両替のルールのちょっとした差で\n国のお金がゆれた", "両替のルールの、ちょっとした差。それだけで、国のお金がゆれちゃうんだよね。"),
    ("question", "……キミが幕府の役人なら\nどうやって止める？", "キミが幕府の役人だったら、どうやって止める？"),
]

def font(path, size): return ImageFont.truetype(path, size)

# The narration voice is shared by every Teacher YAMA video: tools/voice/tts.py (AivisSpeech 阿井田 茂,
# then VOICEVOX, then Open JTalk). Start the engine with: bash tools/voice/aivis_up.sh
sys.path.insert(0, os.path.join(OUT, "..", "..", "..", "tools", "voice"))
from tts import synthesize as tts  # noqa: E402

def center(d, xy, text, f, fill, spacing=18):
    d.multiline_text(xy, text, font=f, fill=fill, anchor="mm", align="center", spacing=spacing)

def arrow(d, a, b, color, w=12, head=40):
    d.line([a, b], fill=color, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        d.line([b, (b[0] - head * math.cos(ang + s * .5), b[1] - head * math.sin(ang + s * .5))], fill=color, width=w)

# --- coins ---------------------------------------------------------------------------------------
def yogin(d, x, y, r=46):        # foreign silver dollar: round, silver
    d.ellipse([x - r, y - r, x + r, y + r], fill=SILVER, outline=SILVER_DK, width=5)
    d.ellipse([x - r * .7, y - r * .7, x + r * .7, y + r * .7], outline=SILVER_DK, width=3)
    center(d, (x, y), "洋", font(BOLD, int(r * .8)), SILVER_DK)

def ichibu(d, x, y, s=40):       # 一分銀: small rectangle, silver
    d.rounded_rectangle([x - s * .6, y - s, x + s * .6, y + s], radius=6, fill=SILVER, outline=SILVER_DK, width=4)
    center(d, (x, y), "一\n分", font(BOLD, int(s * .62)), SILVER_DK, 2)

def koban(d, x, y, s=60):        # 小判: gold oval
    d.ellipse([x - s * .62, y - s, x + s * .62, y + s], fill=GOLD, outline=GOLD_DK, width=6)
    for k in (-.45, -.15, .15, .45):
        d.line([(x - s * .4, y + s * k), (x + s * .4, y + s * k)], fill=GOLD_DK, width=2)
    center(d, (x, y), "両", font(BOLD, int(s * .55)), INK)

def row(fn, n, cx, y, gap, **kw):
    x0 = cx - gap * (n - 1) / 2
    for i in range(n): fn(d_global, x0 + i * gap, y, **kw)

def ship(d, x, y, s=1.0):
    d.polygon([(x - 200 * s, y), (x + 200 * s, y), (x + 150 * s, y + 70 * s), (x - 150 * s, y + 70 * s)], fill=INK)
    d.line([(x, y), (x, y - 220 * s)], fill=INK, width=int(10 * s))
    d.polygon([(x + 8, y - 210 * s), (x + 8, y - 40 * s), (x + 150 * s, y - 60 * s)], fill=PAPER, outline=INK)
    d.polygon([(x - 8, y - 190 * s), (x - 8, y - 50 * s), (x - 120 * s, y - 70 * s)], fill=PAPER, outline=INK)

d_global = None

def art(d, scene):
    global d_global; d_global = d
    cx, cy = W // 2, 760
    if scene == "hook":
        koban(d, 230, cy + 60, 70)
        arrow(d, (330, cy + 60), (460, cy + 60), INK)
        for i, x in enumerate((600, 750, 900)): koban(d, x, cy + 60, 70)
        center(d, (cx, cy - 230), "×3？", font(BOLD, 200), RED)
    elif scene == "bakumatsu":
        center(d, (cx, cy - 170), "幕末", font(BOLD, 220), INK)
        row(koban, 5, cx, cy + 140, 160, s=62)
    elif scene == "port":
        center(d, (cx, cy - 290), "1859年 開港", font(BOLD, 96), RED)
        d.rectangle([0, cy + 130, W, cy + 300], fill=(190, 205, 220))
        ship(d, cx + 120, cy + 120, 1.1)
        center(d, (210, cy + 40), "横浜\n長崎\n函館", font(BOLD, 52), INK, 8)
    elif scene == "rate1":
        yogin(d, 220, cy, 90)
        center(d, (400, cy), "＝", font(BOLD, 120), INK)
        for i in range(3): ichibu(d, 560 + i * 150, cy, 70)
        center(d, (220, cy + 150), "洋銀1枚", font(BOLD, 52), INK)
        center(d, (710, cy + 150), "一分銀3枚", font(BOLD, 52), INK)
    elif scene == "rate2":
        for i in range(4): ichibu(d, 140 + i * 120, cy, 62)
        center(d, (640, cy), "＝", font(BOLD, 120), INK)
        koban(d, 850, cy, 110)
        center(d, (320, cy + 150), "一分銀4枚", font(BOLD, 52), INK)
        center(d, (850, cy + 150), "小判1枚", font(BOLD, 52), INK)
    elif scene == "cheap":
        for x, label, col, note in ((280, "日本", RED, "金が安い"), (800, "外国", INK, "金が高い")):
            d.rounded_rectangle([x - 210, cy - 260, x + 210, cy + 200], radius=30, fill=(255, 255, 255), outline=col, width=8)
            center(d, (x, cy - 190), label, font(BOLD, 80), col)
            koban(d, x, cy - 30, 70)
            center(d, (x, cy + 120), note, font(BOLD, 60), col)
    elif scene == "chain":
        steps = [("洋銀4枚", lambda x, y: [yogin(d, x - 45 + (i % 2) * 90, y - 45 + (i // 2) * 90, 40) for i in range(4)]),
                 ("一分銀12枚", lambda x, y: [ichibu(d, x - 75 + (i % 4) * 50, y - 60 + (i // 4) * 60, 26) for i in range(12)]),
                 ("小判3枚", lambda x, y: [koban(d, x - 70 + i * 70, y, 50) for i in range(3)])]
        for i, (label, draw) in enumerate(steps):
            x = 190 + i * 350
            draw(x, cy - 80)
            center(d, (x, cy + 80), label, font(BOLD, 46), INK)
            if i < 2: arrow(d, (x + 120, cy - 80), (x + 225, cy - 80), RED, 10, 30)
        center(d, (cx, cy + 230), "外国で銀に替えると……", font(BOLD, 64), RED)
    elif scene == "triple":
        for i in range(12): yogin(d, 180 + (i % 6) * 144, cy - 120 + (i // 6) * 140, 56)
        center(d, (cx, cy + 210), "4枚 → 12枚", font(BOLD, 110), RED)
    elif scene == "rule":
        d.rounded_rectangle([200, cy - 260, 880, cy + 160], radius=24, fill=(255, 255, 255), outline=INK, width=6)
        center(d, (cx, cy - 170), "条約", font(BOLD, 90), INK)
        for k in range(3): d.line([(290, cy - 70 + k * 60), (790, cy - 70 + k * 60)], fill=SOFT, width=14)
        d.ellipse([650, cy - 20, 870, cy + 200], outline=RED, width=12)
        center(d, (760, cy + 90), "正式", font(BOLD, 70), RED)
    elif scene == "outflow":
        d.rectangle([0, cy + 160, W, cy + 320], fill=(190, 205, 220))
        ship(d, 800, cy + 150, 0.9)
        for i, (x, y) in enumerate(((180, cy - 40), (330, cy - 120), (470, cy - 60), (600, cy - 170))):
            koban(d, x, y, 55)
        arrow(d, (200, cy + 90), (620, cy + 90), RED)
        center(d, (300, cy - 280), "日本 →", font(BOLD, 72), INK)
        center(d, (800, cy - 280), "外国", font(BOLD, 72), INK)
    elif scene == "fix":
        koban(d, 300, cy - 40, 150)
        center(d, (300, cy + 160), "それまでの小判", font(BOLD, 48), INK)
        arrow(d, (510, cy - 40), (620, cy - 40), INK)
        koban(d, 800, cy - 40, 150)
        d.rounded_rectangle([700, cy - 120, 900, cy + 40], radius=20, fill=PAPER, outline=RED, width=6)
        center(d, (800, cy - 40), "金\n1/3", font(BOLD, 60), RED, 4)
        center(d, (800, cy + 160), "万延小判", font(BOLD, 56), RED)
    elif scene == "price":
        d.polygon([(260, cy - 160), (700, cy - 160), (800, cy - 40), (700, cy + 80), (260, cy + 80)], fill=(255, 255, 255), outline=INK)
        d.line([(260, cy - 160), (700, cy - 160), (800, cy - 40), (700, cy + 80), (260, cy + 80), (260, cy - 160)], fill=INK, width=8)
        center(d, (480, cy - 40), "ねだん", font(BOLD, 96), INK)
        arrow(d, (900, cy + 140), (900, cy - 260), RED, 22, 70)
    elif scene == "close":
        d.line([(180, cy + 30), (900, cy - 50)], fill=INK, width=16)
        d.polygon([(cx - 60, cy + 180), (cx + 60, cy + 180), (cx, cy - 10)], fill=INK)
        koban(d, 300, cy - 70, 70)
        for i in range(3): yogin(d, 720 + i * 80, cy - 150, 38)
        center(d, (cx, cy - 320), "ルールのちょっとした差", font(BOLD, 64), INK)
    elif scene == "question":
        center(d, (cx, cy - 120), "？", font(BOLD, 360), RED)
        center(d, (cx, cy + 190), "キミならどうする？", font(BOLD, 72), INK)

def slide(scene, sub, idx, total, path):
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 250], fill=INK)
    center(d, (W // 2, 105), TITLE, font(BOLD, 78), PAPER)
    center(d, (W // 2, 195), GRADE, font(REG, 40), GOLD)
    art(d, scene)
    d.rounded_rectangle([60, 1110, W - 60, 1420], radius=36, fill=(255, 255, 255), outline=INK, width=6)
    center(d, (W // 2, 1265), sub, font(BOLD, 58), INK, 22)
    d.rectangle([0, H - 26, W, H], fill=SOFT)
    d.rectangle([0, H - 26, int(W * (idx + 1) / total), H], fill=RED)
    im.save(path)

def main():
    os.makedirs(f"{OUT}/build", exist_ok=True)
    lines, t = [], 0.0
    for i, (scene, sub, read) in enumerate(SCRIPT):
        wav, png = f"{OUT}/build/{i:02d}.wav", f"{OUT}/build/{i:02d}.png"
        dur = tts(read, wav) + 0.12          # short breath between lines
        slide(scene, sub, i, len(SCRIPT), png)
        lines.append({"png": png, "wav": wav, "start": t, "dur": dur, "sub": sub})
        t += dur
    lines[-1]["dur"] += 0.8; t += 0.8        # hold the last slide so the closing line can be read
    json.dump(lines, open(f"{OUT}/build/timeline.json", "w"), ensure_ascii=False, indent=1)
    print(f"{len(lines)} lines, {t:.1f}s total")
    render(lines)

def render(lines, name=NAME):
    """One MP4 segment per line (still slide + its narration), joined, loudness set to -14 LUFS for
    YouTube, plus a matching .srt."""
    segs = []
    for i, l in enumerate(lines):
        seg = f"{OUT}/build/seg{i:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", l["png"],
            "-i", l["wav"], "-af", "apad,aresample=48000", "-t", f"{l['dur']:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "160k", "-ac", "2", seg], check=True)
        segs.append(seg)
    with open(f"{OUT}/build/list.txt", "w") as f:
        f.write("".join(f"file '{os.path.basename(s)}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/build/list.txt",
        "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", f"{OUT}/{name}.mp4"], check=True)
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
    with open(f"{OUT}/{name}.srt", "w", encoding="utf-8") as f:
        for i, l in enumerate(lines, 1):
            f.write(f"{i}\n{ts(l['start'])} --> {ts(l['start'] + l['dur'] - 0.12)}\n{l['sub']}\n\n")
    print(f"wrote {name}.mp4 and {name}.srt")

if __name__ == "__main__":
    main()

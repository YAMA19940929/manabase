#!/usr/bin/env python3
"""Build a 9:16 YouTube Short explaining 参勤交代 for 6th graders.

Each subtitle line is voiced separately with Open JTalk, so every slide lasts exactly as long as
its narration. Slides are drawn with Pillow, then ffmpeg joins slides + audio into an MP4.
"""
import json, math, os, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"

PAPER, INK, RED, GOLD, SOFT = (246, 239, 224), (34, 42, 74), (196, 58, 40), (214, 160, 52), (226, 214, 190)

# (scene, subtitle shown on screen, text read aloud). Reading text uses kana where Open JTalk
# would otherwise misread a word.
SCRIPT = [
    ("hook",   "もしキミが大名だったら\n1年おきに家族を置いて江戸へ", "もしキミが大名だったら。1年おきに、家族を置いて江戸まで行かなきゃいけない。"),
    ("hook",   "しかも旅のお金はぜんぶ自分持ち\nなんで従ったんだろう？", "しかも旅のお金は、ぜんぶ自分持ち。なんでそんなのに従ったんだろう？"),
    ("name",   "これが「参勤交代」\n江戸幕府が決めたルールね", "これが、参勤交代。江戸幕府が決めたルールね。"),
    ("year",   "始めたのは3代将軍・徳川家光\n1635年のこと", "始めたのは、3代将軍の徳川家光。1635年のこと。"),
    ("map",    "1年は自分の国、次の1年は江戸\nこれをずーっとくり返す", "1年は自分の国、次の1年は江戸。これを、ずーっとくり返す。"),
    ("family", "で、奥さんと子どもは……\n江戸に住みっぱなし", "で、奥さんと子どもはどうしてたかっていうと、江戸に住みっぱなし。"),
    ("parade", "行列は何百人。宿もごはん代も\nぜんぶ大名が払う", "行列は何百人。泊まるところも、ごはん代も、ぜんぶ大名が払う。"),
    ("parade", "いや、正直これはきつい", "いや、正直これはきつい。"),
    ("power",  "でも幕府からしたら\nそこがねらい", "でも幕府からしたら、そこがねらい。"),
    ("power",  "お金がなかったら\n戦なんてしてられないでしょ？", "お金がなかったら、いくさなんてしてられないでしょ？"),
    ("road",   "ただね、話はここで終わらない", "ただね、話はここで終わらない。"),
    ("road",   "宿場町がにぎわって\n江戸のはやりも地方へ広がった", "行列が通るから、宿場町がにぎわって、江戸のはやりも、地方に広がっていった。"),
    ("japan",  "大名をしばるはずの決まりが\n日本中をつないでた", "大名をしばるはずの決まりが、気づいたら、日本じゅうをつないでた。"),
    ("japan",  "……ちょっとおもしろくない？", "ちょっと、おもしろくない？"),
]

def font(path, size): return ImageFont.truetype(path, size)

# VOICEVOX (https://voicevox.hiroshiba.jp/) gives a far more natural voice than Open JTalk. Run the
# engine with: docker run -d -p 127.0.0.1:50021:50021 voicevox/voicevox_engine:cpu-latest
# The description must credit the voice as "VOICEVOX:<character>" (see each character's terms).
VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021")
VOICEVOX_SPEAKER = int(os.environ.get("VOICEVOX_SPEAKER", "11"))   # 11 = 玄野武宏 ノーマル

def voicevox(text, path):
    import urllib.parse, urllib.request
    q = urllib.parse.urlencode({"text": text, "speaker": VOICEVOX_SPEAKER})
    with urllib.request.urlopen(urllib.request.Request(f"{VOICEVOX_URL}/audio_query?{q}", method="POST"), timeout=60) as r:
        query = json.load(r)
    query.update(speedScale=1.08, intonationScale=1.15, prePhonemeLength=0.05, postPhonemeLength=0.12)
    req = urllib.request.Request(f"{VOICEVOX_URL}/synthesis?speaker={VOICEVOX_SPEAKER}",
                                 data=json.dumps(query).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())

def tts(text, path):
    try:
        voicevox(text, path)
    except OSError:
        print("VOICEVOX not reachable - falling back to Open JTalk", file=sys.stderr)
        subprocess.run(["open_jtalk", "-x", DIC, "-m", VOICE, "-r", "1.35", "-fm", "1.5",
                        "-ow", path], input=text.encode(), check=True)
    with wave.open(path) as w: return w.getnframes() / w.getframerate()

def center(d, xy, text, f, fill, spacing=18):
    d.multiline_text(xy, text, font=f, fill=fill, anchor="mm", align="center", spacing=spacing)

def person(d, x, y, s, color):
    d.ellipse([x - s * .32, y - s, x + s * .32, y - s * .36], fill=color)
    d.rounded_rectangle([x - s * .45, y - s * .3, x + s * .45, y + s * .7], radius=s * .2, fill=color)

def house(d, x, y, s, wall, roof):
    d.rectangle([x - s, y - s * .6, x + s, y + s * .6], fill=wall)
    d.polygon([(x - s * 1.25, y - s * .55), (x, y - s * 1.35), (x + s * 1.25, y - s * .55)], fill=roof)

def arrow(d, a, b, color, w=14):
    d.line([a, b], fill=color, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        d.line([b, (b[0] - 46 * math.cos(ang + s * .5), b[1] - 46 * math.sin(ang + s * .5))], fill=color, width=w)

def art(d, scene):
    cx, cy = W // 2, 760
    if scene == "hook":
        for i in range(7): person(d, 170 + i * 125, cy + 120, 70, INK if i != 3 else RED)
        center(d, (cx, cy - 210), "？", font(BOLD, 360), RED)
    elif scene == "year":
        center(d, (cx, cy - 170), "1635年", font(BOLD, 190), RED)
        center(d, (cx, cy + 50), "3代将軍", font(BOLD, 70), INK)
        center(d, (cx, cy + 150), "徳川家光", font(BOLD, 120), INK)
    elif scene == "map":
        d.ellipse([110, cy - 150, 410, cy + 150], fill=SOFT, outline=INK, width=8)
        d.ellipse([670, cy - 150, 970, cy + 150], fill=SOFT, outline=RED, width=8)
        center(d, (260, cy), "領地", font(BOLD, 84), INK)
        center(d, (820, cy), "江戸", font(BOLD, 84), RED)
        arrow(d, (430, cy - 50), (650, cy - 50), INK); arrow(d, (650, cy + 50), (430, cy + 50), INK)
        center(d, (cx, cy - 250), "1年ごとに交代", font(BOLD, 72), INK)
    elif scene == "parade":
        for i in range(8): person(d, 110 + i * 123, cy - 40, 62, INK if i else RED)
        for i in range(5):
            x = 330 + i * 105
            d.ellipse([x - 48, cy + 170, x + 48, cy + 266], fill=GOLD, outline=(150, 105, 25), width=6)
            d.rectangle([x - 14, cy + 204, x + 14, cy + 232], fill=PAPER)
        center(d, (cx, cy - 250), "何百人もの行列", font(BOLD, 76), INK)
    elif scene == "power":
        d.line([(160, cy + 40), (920, cy - 60)], fill=INK, width=16)
        d.polygon([(cx - 60, cy + 170), (cx + 60, cy + 170), (cx, cy - 5)], fill=INK)
        d.rounded_rectangle([150, cy - 170, 420, cy + 20], radius=24, fill=RED)
        center(d, (285, cy - 75), "幕府", font(BOLD, 88), PAPER)
        d.rounded_rectangle([730, cy - 220, 910, cy - 90], radius=20, fill=SOFT, outline=INK, width=6)
        center(d, (820, cy - 155), "大名", font(BOLD, 58), INK)
        center(d, (cx, cy - 330), "幕府が強く、大名は弱く", font(BOLD, 64), INK)
    elif scene == "road":
        d.rectangle([0, cy + 110, W, cy + 210], fill=SOFT)
        for i, x in enumerate(range(150, 1000, 190)):
            house(d, x, cy - 10, 70, PAPER if i % 2 else SOFT, INK if i % 2 else RED)
            d.rectangle([x - 70, cy - 52, x + 70, cy + 52], outline=INK, width=5)
        center(d, (cx, cy - 250), "街道・宿場町", font(BOLD, 80), INK)
    elif scene == "name":
        center(d, (cx, cy - 150), "さんきんこうたい", font(BOLD, 56), RED)
        center(d, (cx, cy), "参勤交代", font(BOLD, 200), INK)
        d.rectangle([180, cy + 150, 900, cy + 162], fill=RED)
    elif scene == "family":
        d.ellipse([110, cy - 150, 410, cy + 150], fill=SOFT, outline=INK, width=8)
        d.ellipse([670, cy - 150, 970, cy + 150], fill=SOFT, outline=RED, width=8)
        center(d, (260, cy), "領地", font(BOLD, 84), INK)
        center(d, (820, cy - 70), "江戸", font(BOLD, 72), RED)
        person(d, 790, cy + 95, 58, RED); person(d, 865, cy + 105, 40, RED)
        arrow(d, (430, cy), (650, cy), INK)
        center(d, (cx, cy - 250), "家族は江戸に", font(BOLD, 72), INK)
    elif scene == "japan":
        pts = [(880, 250), (800, 380), (700, 520), (600, 640), (480, 720), (360, 790), (240, 860), (150, 960)]
        # fit the route between the header (y~300) and the subtitle box (y~1110)
        pts = [(x, round(340 + (y - 250) * 700 / 710)) for x, y in pts]
        d.line(pts, fill=INK, width=14, joint="curve")
        for i, (x, y) in enumerate(pts):
            r = 30 if i == 3 else 18
            d.ellipse([x - r, y - r, x + r, y + r], fill=RED if i == 3 else PAPER, outline=INK, width=6)
        center(d, (pts[3][0] + 130, pts[3][1] - 10), "江戸", font(BOLD, 64), RED)
        center(d, (300, 470), "日本中が\nつながった", font(BOLD, 72), INK, 16)

def slide(scene, sub, idx, total, path):
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 250], fill=INK)
    center(d, (W // 2, 105), "参勤交代ってなに？", font(BOLD, 78), PAPER)
    center(d, (W // 2, 195), "小6社会", font(REG, 40), GOLD)
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
    json.dump(lines, open(f"{OUT}/build/timeline.json", "w"), ensure_ascii=False, indent=1)
    print(f"{len(lines)} lines, {t:.1f}s total")
    render(lines)

def render(lines, name="sankin_kotai_short"):
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

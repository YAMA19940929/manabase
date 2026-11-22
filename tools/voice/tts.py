#!/usr/bin/env python3
"""tts.py - Teacher YAMA の説明動画の読み上げ(共通部品)。

基本の声は AivisSpeech の「阿井田 茂」ノーマル(2026-11-22 にオーナーが採用)。

    from tts import synthesize          # tools/voice を sys.path に入れてから
    seconds = synthesize("読む文", "out.wav")

    python3 tools/voice/tts.py "読む文" out.wav     # 単体で試す

使うエンジンは次の順に試し、最初に動いたものを使う。どれを使ったかは標準エラーに1回だけ出す。
  1. AivisSpeech  http://127.0.0.1:10101  (tools/voice/aivis_up.sh で起動)
  2. VOICEVOX     http://127.0.0.1:50021
  3. Open JTalk   (apt の open-jtalk)
声を変えるときは環境変数で:
  AIVIS_SPEAKER="阿井田 茂"  AIVIS_STYLE="ノーマル"  (AivisHub のモデル UUID は AIVIS_MODEL_UUID)

ライセンス:阿井田 茂(CV:古山キリヲ)は Aivis Common Model License (ACML) 1.0。営利利用可、クレジット任意。
本人や公式と誤解させる使い方、誹謗中傷、虚偽情報、政治・宗教の宣伝などは禁止。
"""
import json, os, subprocess, sys, urllib.error, urllib.parse, urllib.request, wave

AIVIS_URL = os.environ.get("AIVIS_URL", "http://127.0.0.1:10101")
AIVIS_SPEAKER = os.environ.get("AIVIS_SPEAKER", "阿井田 茂")
AIVIS_STYLE = os.environ.get("AIVIS_STYLE", "ノーマル")
AIVIS_MODEL_UUID = os.environ.get("AIVIS_MODEL_UUID", "47e53151-a378-46f3-abee-ce13aa07feb1")  # 阿井田 茂 on AivisHub
VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021")
VOICEVOX_SPEAKER = int(os.environ.get("VOICEVOX_SPEAKER", "11"))   # 11 = 玄野武宏 ノーマル
OJT_DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
OJT_VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"

_announced = set()
def _say(engine, detail=""):
    if engine not in _announced:
        _announced.add(engine)
        print(f"[tts] {engine}{' - ' + detail if detail else ''}", file=sys.stderr)

def _post(url, data=None, timeout=300):
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _speakers(base):
    with urllib.request.urlopen(f"{base}/speakers", timeout=10) as r:
        return json.load(r)

def _norm(s): return s.replace(" ", "").replace("　", "")

_aivis_style_id = None
def aivis_style_id():
    """名前で話者とスタイルを探す。入っていなければ AivisHub から入れる。"""
    global _aivis_style_id
    if _aivis_style_id is not None:
        return _aivis_style_id
    def find():
        for s in _speakers(AIVIS_URL):
            if _norm(s["name"]) == _norm(AIVIS_SPEAKER):
                for st in s["styles"]:
                    if st["name"] == AIVIS_STYLE:
                        return st["id"]
                raise SystemExit(f"{AIVIS_SPEAKER} has no style {AIVIS_STYLE}: "
                                 + ", ".join(st["name"] for st in s["styles"]))
    sid = find()
    if sid is None:
        _say("AivisSpeech", f"installing {AIVIS_SPEAKER} from AivisHub")
        url = f"https://api.aivis-project.com/v1/aivm-models/{AIVIS_MODEL_UUID}/download?model_type=AIVMX"
        body = urllib.parse.urlencode({"url": url}).encode()
        req = urllib.request.Request(f"{AIVIS_URL}/aivm_models/install", data=body, method="POST")
        urllib.request.urlopen(req, timeout=900).read()
        sid = find()
    _aivis_style_id = sid
    return sid

def _engine_tts(base, speaker, text, path, tweak=None):
    q = urllib.parse.urlencode({"text": text, "speaker": speaker})
    query = json.loads(_post(f"{base}/audio_query?{q}", timeout=120))
    if tweak: query.update(tweak)
    with open(path, "wb") as f:
        f.write(_post(f"{base}/synthesis?speaker={speaker}", json.dumps(query).encode()))

def synthesize(text, path):
    """text を読んだ WAV を path に書き、長さ(秒)を返す。"""
    try:
        sid = aivis_style_id()
        _engine_tts(AIVIS_URL, sid, text, path, {"prePhonemeLength": 0.05, "postPhonemeLength": 0.12})
        _say("AivisSpeech", f"{AIVIS_SPEAKER} {AIVIS_STYLE}")
    except (OSError, urllib.error.URLError) as e:
        try:
            _engine_tts(VOICEVOX_URL, VOICEVOX_SPEAKER, text, path,
                        {"speedScale": 1.08, "intonationScale": 1.15, "prePhonemeLength": 0.05, "postPhonemeLength": 0.12})
            _say("VOICEVOX", f"AivisSpeech not reachable ({e.__class__.__name__}); speaker {VOICEVOX_SPEAKER}. "
                             "Credit VOICEVOX in the description.")
        except (OSError, urllib.error.URLError):
            _say("Open JTalk", "AivisSpeech and VOICEVOX not reachable - robotic voice")
            subprocess.run(["open_jtalk", "-x", OJT_DIC, "-m", OJT_VOICE, "-r", "1.35", "-fm", "1.5", "-ow", path],
                           input=text.encode(), check=True)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    print(f"{synthesize(sys.argv[1], sys.argv[2]):.2f}s")

#!/usr/bin/env python3
"""hookscore.py - score a YouTube hook before you waste a take on it.

Five properties, 0-100 each, and a verdict that is 60% the mean and 40% the weakest one. The
weakest-link weighting is deliberate: a hook with four strong properties and one dead one is a hook
that leaks at the dead one, and averaging hides that.

    python3 hookscore.py hooks.txt            # one hook per line, ranked
    python3 hookscore.py --hook "one line"    # score a single hook
    python3 hookscore.py --json hooks.txt     # machine-readable

WHAT THIS CAN AND CANNOT TELL YOU. Measured against 74 real short-form hooks (first 15 seconds of
auto-captions, top-8 and bottom-8 by views across five channels): it separates deliberately bad
hooks from real ones well, and it separates a creator's own hits from their own misses barely at
all. Treat a low score as a reason to look again, never a high score as a promise.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORMULAS = json.load(open(os.path.join(HERE, "hooks.json")))["hooks"]

FILLER = {"basically","actually","literally","just","really","very","so","kind","sort","like",
          "guys","hey","welcome","today","video","subscribe","channel"}
VAGUE = {"amazing","incredible","insane","crazy","huge","massive","game","changer","secret",
         "powerful","ultimate","best","revolutionary","mind","blowing","unbelievable"}
CONCRETE = re.compile(r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b", re.I)
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I)
STAKE = re.compile(r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b", re.I)
CURIOSITY = re.compile(r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b", re.I)

def words(t): return re.findall(r"[a-z0-9'%$.]+", t.lower())

# --- Japanese -------------------------------------------------------------------------------------
# Japanese has no spaces, so the English word lists never fire on it and every property sits at its
# floor. A hook containing kana or kanji is scored by the same five properties with Japanese cues.
# BREVITY counts characters: spoken Japanese runs about 5-6 characters a second, so 15-50 characters
# is the band that lands inside the same ~10 seconds the 9-24 word English band does.
JA_TEXT = re.compile(r"[぀-ヿ㐀-鿿]")
JA_NUM = r"[0-9０-９一二三四五六七八九十百千万億]"
JA_CONCRETE = re.compile(JA_NUM + r"+\s?(%|％|割|倍|人|円|年|か月|ヶ月|週間|日|時間|分|秒|回|本|個|つ|位|代|歳|km|キロ)")
JA_VAGUE = re.compile(r"(すごい|スゴい|ヤバい|やばい|最強|神|衝撃|驚愕|究極|完璧|革命|半端ない|エグい)")
JA_FILLER = re.compile(r"(えー|えっと|あの[ーぉ]|どうも|こんにちは|はじめまして|チャンネル登録|今日は|今回は|ということで)")
# Japanese usually drops あなた, so "もし小6で歴史が苦手なら" or "〜な人は" is the address.
JA_YOU = re.compile(r"(あなた|君|きみ|キミ|みんな|みなさん|皆さん|もし[^。、]{1,16}なら|[^。、]{1,12}な?人(は|へ|に))")
JA_STAKE = re.compile(r"(損|失敗|やめ|無駄|ムダ|危険|手遅れ|後悔|知らないと|しないと|できないと|前に|二度と|ダメ|だめ|間違|ミス|負担|命)")
JA_CURIOSITY = re.compile(r"(なぜ|どうして|なんで|どうやって|何|なに|いったい|実は|本当は|ところが|でも|しかし|だけ|しか|理由|秘密|まさか)")
JA_CLOSED = re.compile(r"(だから|なので|ため(に)?|つまり)")
JA_NAMED = re.compile(r"「[^」]+」|[ァ-ヺ][ァ-ーー]{2,}")

def ja_specificity(t):
    s = 34 + len(JA_CONCRETE.findall(t)) * 22 - len(JA_VAGUE.findall(t)) * 16 - len(JA_FILLER.findall(t)) * 5
    s += min(18, 6 * len(JA_NAMED.findall(t)))
    return max(0, min(100, s))

def ja_address(t):
    first = 30 if JA_YOU.search(t[:12]) else 0
    return max(0, min(100, 26 + len(JA_YOU.findall(t)) * 20 + first))

def ja_stakes(t):
    return max(0, min(100, 22 + len(JA_STAKE.findall(t)) * 26 + (14 if JA_CONCRETE.search(t) else 0)))

def ja_curiosity(t):
    q = 18 if re.search(r"[?？]\s*$", t.strip()) else 0
    closed = -18 if JA_CLOSED.search(t) else 0
    return max(0, min(100, 24 + len(JA_CURIOSITY.findall(t)) * 17 + q + closed))

def ja_brevity(t):
    n = len(re.sub(r"[\s、。,.!?！？「」『』…・]", "", t))
    if n == 0: return 0
    if 15 <= n <= 50: return 100
    if n < 15: return max(30, 100 - (15 - n) * 7)
    return max(10, 100 - (n - 50) * 4)

def specificity(t):
    w = words(t)
    if not w: return 0
    nums = len(CONCRETE.findall(t))
    vague = sum(1 for x in w if x in VAGUE)
    filler = sum(1 for x in w if x in FILLER)
    s = 34 + nums * 22 - vague * 16 - filler * 5
    # proper nouns that are not sentence-initial read as named things
    s += min(18, 6 * sum(1 for x in t.split()[1:] if x[:1].isupper()))
    return max(0, min(100, s))

def address(t):
    n = len(YOU.findall(t))
    first = 30 if YOU.search(" ".join(t.split()[:6])) else 0
    return max(0, min(100, 26 + n * 20 + first))

def stakes(t):
    n = len(STAKE.findall(t))
    return max(0, min(100, 22 + n * 26 + (14 if CONCRETE.search(t) else 0)))

def curiosity(t):
    n = len(CURIOSITY.findall(t))
    q = 18 if t.strip().endswith("?") else 0
    # a hook that resolves itself has no gap left
    closed = -18 if re.search(r"\b(because|so that|which means)\b", t, re.I) else 0
    return max(0, min(100, 24 + n * 17 + q + closed))

def brevity(t):
    n = len(words(t))
    if n == 0: return 0
    # 9-24 words is the band a spoken hook lands in at ~150wpm inside 10 seconds
    if 9 <= n <= 24: return 100
    if n < 9:  return max(30, 100 - (9 - n) * 11)
    return max(10, 100 - (n - 24) * 7)

PROPS = [("SPECIFICITY", specificity), ("ADDRESS", address), ("STAKES", stakes),
         ("CURIOSITY", curiosity), ("BREVITY", brevity)]
JA_PROPS = [("SPECIFICITY", ja_specificity), ("ADDRESS", ja_address), ("STAKES", ja_stakes),
            ("CURIOSITY", ja_curiosity), ("BREVITY", ja_brevity)]

def is_ja(t): return bool(JA_TEXT.search(t))

def classify(t):
    key = "match_ja" if is_ja(t) else "match"
    best, hits = None, 0
    for f in FORMULAS:
        n = sum(1 for p in f.get(key, []) if re.search(p, t, re.I))
        if n > hits: best, hits = f, n
    return (best["name"] if best else "Unclassified"), hits

def score(t):
    parts = {n: fn(t) for n, fn in (JA_PROPS if is_ja(t) else PROPS)}
    vals = list(parts.values())
    verdict = round(0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals))
    name, hits = classify(t)
    return parts, verdict, name, hits

def band(v): return "STRONG" if v >= 72 else "WORKABLE" if v >= 55 else "WEAK"

def report(t, parts, verdict, name, hits):
    print(f"\n  {t.strip()}")
    print(f"  {'-' * min(72, max(20, len(t.strip())))}")
    for k, v in parts.items():
        print(f"    {k:<12} {v:3d}  {'#' * (v // 5)}")
    print(f"    {'VERDICT':<12} {verdict:3d}  {band(verdict)}")
    print(f"    formula      {name}" + (f"  ({hits} pattern{'s' if hits != 1 else ''} matched)" if hits else "  (no formula matched - that is usually a summary, not a hook)"))
    low = min(parts, key=parts.get)
    print(f"    weakest      {low} - {(FIX_JA if is_ja(t) else FIX)[low]}")

FIX = {
 "SPECIFICITY": "swap one adjective for a number, a name or a date",
 "ADDRESS": "say 'you' in the first six words",
 "STAKES": "name what it costs them to keep doing it the current way",
 "CURIOSITY": "cut the half of the sentence that answers itself",
 "BREVITY": "9 to 24 words. Read it out loud and stop where you run out of breath",
}
FIX_JA = {
 "SPECIFICITY": "形容詞を1つ、数字・名前・年号に置き換える",
 "ADDRESS": "最初の12文字以内に「あなた」「みんな」など、見ている人への呼びかけを入れる",
 "STAKES": "知らないまま・今のやり方のままだと何を損するかを言う",
 "CURIOSITY": "答えまで言ってしまっている後半を削り、「なぜ？」を残す",
 "BREVITY": "15〜50文字に。声に出して、息が続くところで切る",
}

def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    if "--hook" in a:
        lines = [a[a.index("--hook") + 1]]
    elif a and os.path.exists(a[0]):
        lines = [l for l in open(a[0]).read().splitlines() if l.strip()]
    else:
        print(__doc__); sys.exit(1 if not a else 0)
    out = []
    for t in lines:
        parts, verdict, name, hits = score(t)
        out.append({"hook": t.strip(), "properties": parts, "verdict": verdict,
                    "band": band(verdict), "formula": name, "matched": hits})
    out.sort(key=lambda r: -r["verdict"])
    if as_json:
        print(json.dumps([{k: v for k, v in r.items() if k != "matched"} for r in out], indent=1)); return
    for r in out:
        report(r["hook"], r["properties"], r["verdict"], r["formula"], r["matched"])
    if len(out) > 1:
        print(f"\n  winner: {out[0]['hook'].strip()}  ({out[0]['verdict']}, {out[0]['band']})\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""title.py - lint a YouTube title and thumbnail pairing before you publish it.

    python3 title.py --title "..." --thumb "AI RAN IT"
    python3 title.py titles.txt            # one per line, ranked
    python3 title.py --title "..." --json

The pairing is the unit, not the title. A title that repeats the thumbnail text wastes half the
click surface, and that is the single most common mistake this checks for.

Length: YouTube truncates around 60 characters on desktop search and around 40 on a mobile home
feed. Both limits are reported because they are different failures - a desktop truncation loses the
tail, a mobile one can lose the subject.
"""
import json, re, sys, os, unicodedata

DESKTOP, MOBILE, HARD = 60, 40, 100

# Japanese: a full-width character takes about two Latin characters of feed width, so truncation is
# judged on display width (full-width = 2) while the 100 limit stays a plain character count, which
# is what YouTube enforces. Words are the kanji/katakana runs, since there are no spaces.
JA_TEXT = re.compile(r"[぀-ヿ㐀-鿿]")
JA_VAGUE = re.compile(r"(すごい|スゴい|ヤバい|やばい|最強|神|衝撃|究極|完璧|完全|革命|エグい|ぜんぶ|全部)")
JA_FILLER_HEAD = re.compile(r"^[\s【】\[\]「」『』()()!！?？・:：]*(どうも|こんにちは|今日は|今回は|みなさん|皆さん|えー|あの)")

def width(t): return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in t)

def head_by_width(t, limit):
    out, w = "", 0
    for c in t:
        w += width(c)
        if w > limit: break
        out += c
    return out

def ja_words(t):
    return set(re.findall(r"[㐀-鿿々]{2,}|[ァ-ヺ][ァ-ーー]+|[a-z0-9]{2,}", t.lower()))
VAGUE = {"amazing","incredible","insane","crazy","huge","massive","ultimate","best","powerful",
         "secret","revolutionary","mindblowing","epic","perfect","complete","everything"}
STOP = {"the","a","an","of","for","to","in","on","and","or","is","are","with","your","you","my","i",
        "this","that","it","how","what","why"}

def words(t): return re.findall(r"[a-z0-9']+", t.lower())

def check(title, thumb=None):
    t = title.strip()
    n = len(t)
    ja = bool(JA_TEXT.search(t))
    issues, good = [], []
    if ja:
        w = width(t)
        if n > HARD: issues.append(("length", f"{n} characters - YouTube's hard limit is {HARD}"))
        elif w > DESKTOP: issues.append(("length", f"{n} characters ({w} wide, full-width counts 2) - desktop search cuts near {DESKTOP} wide, about {DESKTOP // 2} Japanese characters"))
        else: good.append(f"{n} characters ({w} wide), inside the desktop cut")
        if w > MOBILE:
            issues.append(("mobile", f'a mobile feed shows about "{head_by_width(t, MOBILE)}..." - check the subject survives'))
        return finish_ja(t, n, thumb, issues, good)
    if n > HARD: issues.append(("length", f"{n} characters - YouTube's hard limit is {HARD}"))
    elif n > DESKTOP: issues.append(("length", f"{n} characters - desktop search cuts near {DESKTOP}"))
    else: good.append(f"{n} characters, inside the {DESKTOP}-character desktop cut")
    if n > MOBILE:
        head = t[:MOBILE].rsplit(" ", 1)[0]
        issues.append(("mobile", f'a mobile feed shows about "{head}..." - check the subject survives'))
    caps = [w for w in t.split() if len(w) > 2 and w.isupper()]
    if len(caps) > 2: issues.append(("shouting", f"{len(caps)} all-caps words - two is the ceiling before it reads as spam"))
    elif caps: good.append(f"{len(caps)} all-caps word for emphasis")
    v = [w for w in words(t) if w in VAGUE]
    if v: issues.append(("vague", f"{', '.join(sorted(set(v)))} - swap for a number, a name or a date"))
    nums = re.findall(r"\d[\d,.]*%?", t)
    if nums: good.append(f"carries a concrete figure ({', '.join(nums[:3])})")
    else: issues.append(("no-number", "no number, date or name - the most reliable single fix"))
    if t.endswith("?"): good.append("open question in the title")
    front = [w for w in words(t)[:3] if w not in STOP]
    if not front: issues.append(("front-load", "the first three words are all filler - move the subject forward"))
    if thumb:
        tw, hw = set(words(t)) - STOP, set(words(thumb)) - STOP
        shared = tw & hw
        if shared:
            issues.append(("duplicate", f"thumbnail repeats the title on {', '.join(sorted(shared))} - "
                                        "the thumbnail should say what the title does not"))
        else:
            good.append("thumbnail and title carry different words")
        if len(words(thumb)) > 4:
            issues.append(("thumb-length", f"{len(words(thumb))} words on the thumbnail - three is the ceiling at feed size"))
    score = max(0, min(100, 100 - 14 * len(issues) + 4 * len(good)))
    return {"title": t, "chars": n, "score": score, "issues": issues, "good": good}

def finish_ja(t, n, thumb, issues, good):
    v = JA_VAGUE.findall(t)
    if v: issues.append(("vague", f"{', '.join(sorted(set(v)))} - swap for a number, a name or a date"))
    nums = re.findall(r"[0-9０-９][0-9０-９,.]*[%％]?", t)
    if nums: good.append(f"carries a concrete figure ({', '.join(nums[:3])})")
    else: issues.append(("no-number", "no number, date or name - the most reliable single fix"))
    if re.search(r"[?？]", t): good.append("open question in the title")
    if JA_FILLER_HEAD.search(t): issues.append(("front-load", "opens with a greeting or filler - move the subject forward"))
    if thumb:
        shared = ja_words(t) & ja_words(thumb)
        if shared:
            issues.append(("duplicate", f"thumbnail repeats the title on {', '.join(sorted(shared))} - "
                                        "the thumbnail should say what the title does not"))
        else:
            good.append("thumbnail and title carry different words")
        tn = len(re.sub(r"[\s!！?？、。・]", "", thumb))
        if tn > 10:
            issues.append(("thumb-length", f"{tn} characters on the thumbnail - about 10 is the ceiling at feed size"))
    score = max(0, min(100, 100 - 14 * len(issues) + 4 * len(good)))
    return {"title": t, "chars": n, "score": score, "issues": issues, "good": good}

def show(r):
    print(f'\n  "{r["title"]}"')
    print(f"  {r['chars']} chars   score {r['score']}/100")
    for k, m in r["issues"]: print(f"    x  {k:<12} {m}")
    for m in r["good"]:      print(f"    ok              {m}")

def main():
    a = sys.argv[1:]
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    thumb = a[a.index("--thumb") + 1] if "--thumb" in a else None
    if "--title" in a:
        rows = [check(a[a.index("--title") + 1], thumb)]
    elif a and os.path.exists(a[0]):
        rows = [check(l, thumb) for l in open(a[0]).read().splitlines() if l.strip()]
    else:
        print(__doc__); sys.exit(1)
    rows.sort(key=lambda r: -r["score"])
    if as_json: print(json.dumps(rows, indent=1)); return
    for r in rows: show(r)
    print()

if __name__ == "__main__":
    main()

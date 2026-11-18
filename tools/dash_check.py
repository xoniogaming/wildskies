"""Find dashed / stitched lines in a pixel image and flag stubs, uneven gaps and one-sided layouts.

    py tools/dash_check.py <png> [--scale N] [--min-runs 4] [--sheet out.png]

A dashed line = along one row or column, >= min-runs runs of colour C, each <= 4 px, separated by gaps of one single
other colour D (the same D for the whole chain), each gap <= 4 px. For each chain:
  stub   a run shorter than the chain's usual run length (mode), at the ends or inside
  long   a run longer than usual (a dash merged with something)
  gap    a gap that differs from the usual gap by more than 1
  asym   the run/gap layout read from one end differs from the other end by more than 1 px anywhere
"""
import sys
from collections import Counter
from PIL import Image, ImageDraw


def runs_of(line):
    out, s = [], 0
    for i in range(1, len(line) + 1):
        if i == len(line) or line[i] != line[s]:
            out.append((s, i - s, line[s]))
            s = i
    return out


def chains(line, min_runs=4, max_run=4, max_gap=4):
    rs = runs_of(line)
    found = []
    # chain: C,D,C,D,...,C with every C run <= max_run, every D run <= max_gap, D single colour
    i = 0
    covered = set()                       # (run index, colour) already inside a chain of that colour
    while i < len(rs):
        s, n, c = rs[i]
        if c is None or n > max_run or (i, c) in covered:
            i += 1
            continue
        j = i
        d = None
        seq = [rs[i]]
        while j + 2 < len(rs):
            g, r = rs[j + 1], rs[j + 2]
            if g[2] is None or r[2] != c or g[1] > max_gap or r[1] > max_run + 2:
                break
            if d is None:
                d = g[2]
            elif g[2] != d:
                break
            seq += [g, r]
            j += 2
        k = (len(seq) + 1) // 2
        if k >= min_runs:
            found.append((c, d, seq))
            covered.update((t, c) for t in range(i, j + 1, 2))
        i += 1
    return found


def judge(seq):
    rl = [r[1] for r in seq[0::2]]
    gl = [g[1] for g in seq[1::2]]
    L = Counter(rl).most_common(1)[0][0]
    G = Counter(gl).most_common(1)[0][0]
    issues = []
    for idx, r in enumerate(seq[0::2]):
        if r[1] < L:
            issues.append(("stub", r[0], r[1]))
        elif r[1] > L:
            issues.append(("long", r[0], r[1]))
    for g in seq[1::2]:
        if abs(g[1] - G) > 1:
            issues.append(("gap", g[0], g[1]))
    lay = [x[1] for x in seq]
    if any(abs(a - b) > 1 for a, b in zip(lay, lay[::-1])) or sum(abs(a - b) for a, b in zip(lay, lay[::-1])) > 4:
        issues.append(("asym", seq[0][0], seq[-1][0] + seq[-1][1] - seq[0][0]))
    return L, G, issues


def pick(line, found):
    """C-on-D and D-on-C often both fit one line (2 on 2 off). Keep the reading that sits on its gap colour: the
    pixel just past each end is D (the background carries on), ties -> the reading with fewer issues."""
    def score(ch):
        c, d, seq = ch
        s, e = seq[0][0], seq[-1][0] + seq[-1][1]
        return (s > 0 and line[s - 1] == d) + (e < len(line) and line[e] == d)
    keep = []
    for ch in found:
        s, e = ch[2][0][0], ch[2][-1][0] + ch[2][-1][1]
        rival = [o for o in found if o is not ch and o[0] == ch[1] and o[1] == ch[0]
                 and min(e, o[2][-1][0] + o[2][-1][1]) - max(s, o[2][0][0]) > (e - s) // 2]
        if any(score(o) > score(ch) or (score(o) == score(ch) and len(judge(o[2])[2]) < len(judge(ch[2])[2]))
               or (score(o) == score(ch) and len(judge(o[2])[2]) == len(judge(ch[2])[2]) and id(o) < id(ch))
               for o in rival):
            continue
        keep.append(ch)
    return keep


def strict(seq):
    """A regular dashed line (all inner runs = L, all gaps within 1 of G) that ends in a shorter run at one or both
    ends: the stub fault. Returns the issues or []."""
    rl = [r[1] for r in seq[0::2]]
    gl = [g[1] for g in seq[1::2]]
    inner = rl[1:-1]
    if len(inner) < 3 or len(set(inner)) != 1:
        return []
    L = inner[0]
    if L < 2 or max(gl) - min(gl) > 1:
        return []
    out = []
    if rl[0] < L:
        out.append(("stub", seq[0][0], rl[0]))
    if rl[-1] < L:
        out.append(("stub", seq[-1][0], rl[-1]))
    return out


STRICT = False


def scan(im, min_runs=4):
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    col = lambda x, y: px[x, y][:3] if px[x, y][3] > 0 else None  # noqa: E731
    finds = []
    for kind, n, m in (("row", h, w), ("col", w, h)):
        for a in range(n):
            line = [col(b, a) if kind == "row" else col(a, b) for b in range(m)]
            for c, d, seq in pick(line, chains(line, min_runs)):
                L, G, iss = judge(seq)
                if STRICT:
                    iss = strict(seq)
                if iss:
                    finds.append((kind, a, seq[0][0], seq[-1][0] + seq[-1][1] - 1, c, d, L, G, iss))
    return finds


def main():
    a = sys.argv[1:]
    path = a[0]
    scale = int(a[a.index("--scale") + 1]) if "--scale" in a else 1
    mr = int(a[a.index("--min-runs") + 1]) if "--min-runs" in a else 4
    global STRICT
    STRICT = "--strict" in a
    im = Image.open(path).convert("RGBA")
    if scale > 1:
        im = im.resize((im.width // scale, im.height // scale), 0)
    f = scan(im, mr)
    for kind, at, s, e, c, d, L, G, iss in f:
        where = f"y={at} x={s}..{e}" if kind == "row" else f"x={at} y={s}..{e}"
        print(f"{kind} {where} dash{c} on{d} run={L} gap={G}: " + ", ".join(f"{k}@{p}({n})" for k, p, n in iss))
    print(f"{len(f)} flagged lines in {path}")
    if "--sheet" in a and f:
        out = a[a.index("--sheet") + 1]
        z, pad, box = 8, 6, 28
        tiles = []
        for kind, at, s, e, *_ in f[:40]:
            cx, cy = ((s + e) // 2, at) if kind == "row" else (at, (s + e) // 2)
            # show the line's two ends
            for ex, ey in (((s, at), (e, at)) if kind == "row" else ((at, s), (at, e))):
                x0, y0 = max(0, ex - box // 2), max(0, ey - box // 2)
                t = im.crop((x0, y0, x0 + box, y0 + box)).resize((box * z, box * z), 0)
                dr = ImageDraw.Draw(t)
                dr.rectangle(((ex - x0) * z, (ey - y0) * z, (ex - x0 + 1) * z - 1, (ey - y0 + 1) * z - 1), outline=(255, 0, 255))
                tiles.append(t)
        cols = 6
        rows = (len(tiles) + cols - 1) // cols
        sh = Image.new("RGBA", (cols * (box * z + pad), rows * (box * z + pad)), (40, 40, 40, 255))
        for i, t in enumerate(tiles):
            sh.alpha_composite(t, ((i % cols) * (box * z + pad), (i // cols) * (box * z + pad)))
        sh.save(out)


if __name__ == "__main__":
    main()

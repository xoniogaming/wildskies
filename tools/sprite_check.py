"""Checks a GUI texture against the pixel rules (references/pixel-rules.md).

    python sprite_check.py <png> [--soft u,v,w,h ...] [--cell [name=]u,v,w,h ...]
                                 [--grid [name=]u,v,w,h,stepx,stepy,cols,count ...]

Always: the size (power of two?), pixels whose alpha is not 0 or 255 (outside the --soft regions, which are meant to be
soft), and 4x4 windows that are a 50% checker of two colours (dither or a 1-px mesh).
--cell: a frame something should sit centred in; prints the visible box and the room on each side.
--grid: a row/grid of such cells, e.g. 20 px emblem cells from (0,44), 12 across, 16 of them:
        --grid emblem=0,44,20,20,20,20,12,16
Exit code 1 if anything is wrong (soft pixels, checkers, a cell that is off centre or cannot centre).
"""
import sys

from PIL import Image


def ints(s):
    return [int(t) for t in s.split(",")]


def named(s, default):
    if "=" in s:
        n, s = s.split("=", 1)
        return n, s
    return default, s


def pow2(n):
    return n > 0 and n & (n - 1) == 0


def inside(x, y, boxes):
    return any(u <= x < u + w and v <= y < v + h for u, v, w, h in boxes)


def clusters(points):
    """Groups points into bounding boxes of touching 16-px tiles, so a report is a few lines, not thousands."""
    tiles = {}
    for x, y in points:
        tiles.setdefault((x // 16, y // 16), []).append((x, y))
    seen, out = set(), []
    for t in sorted(tiles):
        if t in seen:
            continue
        stack, pts = [t], []
        seen.add(t)
        while stack:
            cx, cy = stack.pop()
            pts += tiles[(cx, cy)]
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (cx + dx, cy + dy)
                    if n in tiles and n not in seen:
                        seen.add(n)
                        stack.append(n)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out.append((min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, len(pts)))
    return out


def checker_at(px, x, y):
    a, b = px[x, y], px[x + 1, y]
    if a == b or (a[3] == 0 and b[3] == 0):
        return False
    for j in range(4):
        for i in range(4):
            if px[x + i, y + j] != (a if (i + j) % 2 == 0 else b):
                return False
    return True


def cell_report(px, name, u, v, w, h):
    xs, ys = [], []
    for y in range(v, v + h):
        for x in range(u, u + w):
            if px[x, y][3]:
                xs.append(x)
                ys.append(y)
    if not xs:
        return "%-28s (%d,%d %dx%d)  empty" % (name, u, v, w, h), True
    l, r = min(xs) - u, u + w - 1 - max(xs)
    t, b = min(ys) - v, v + h - 1 - max(ys)
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    if l == r and t == b:
        verdict, ok = "centred", True
    elif (w - bw) % 2 or (h - bh) % 2:
        verdict, ok = "CANNOT CENTRE: a %dx%d box in a %dx%d cell (parity)" % (bw, bh, w, h), False
    else:
        verdict, ok = "OFF CENTRE: move %+d,%+d" % ((r - l) // 2, (b - t) // 2), False
    return "%-28s (%d,%d %dx%d)  box %dx%d  left %d right %d top %d bottom %d  %s" % (
        name, u, v, w, h, bw, bh, l, r, t, b, verdict), ok


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    path, soft, cells = a[0], [], []
    i = 1
    while i < len(a):
        flag = a[i]
        i += 1
        while i < len(a) and not a[i].startswith("--"):
            if flag == "--soft":
                soft.append(tuple(ints(a[i])))
            elif flag == "--cell":
                n, s = named(a[i], "cell")
                cells.append((n,) + tuple(ints(s)))
            elif flag == "--grid":
                n, s = named(a[i], "grid")
                u, v, w, h, sx, sy, cols, count = ints(s)
                for k in range(count):
                    cells.append(("%s[%d]" % (n, k), u + (k % cols) * sx, v + (k // cols) * sy, w, h))
            else:
                print("unknown option", flag)
                return 2
            i += 1
    im = Image.open(path).convert("RGBA")
    W, H = im.size
    px = im.load()
    bad = False

    ok = pow2(W) and pow2(H)
    print("%s  %dx%d  %s" % (path, W, H, "power of two" if ok else "NOT a power of two: v = y/%d may sample a neighbour" % H))
    bad |= not ok

    semi = [(x, y) for y in range(H) for x in range(W) if 0 < px[x, y][3] < 255 and not inside(x, y, soft)]
    if semi:
        bad = True
        print("alpha: %d pixels are neither 0 nor 255" % len(semi))
        for u, v, w, h, n in clusters(semi):
            print("   %d px around (%d,%d %dx%d)" % (n, u, v, w, h))
    else:
        print("alpha: only 0 and 255" + (" outside the soft regions" if soft else ""))

    chk = [(x, y) for y in range(H - 3) for x in range(W - 3) if not inside(x, y, soft) and checker_at(px, x, y)]
    if chk:
        bad = True
        print("checker: %d 4x4 windows are a two-colour checker (dither or 1-px mesh)" % len(chk))
        for u, v, w, h, n in clusters(chk):
            print("   around (%d,%d %dx%d)" % (u, v, w + 3, h + 3))
    else:
        print("checker: none")

    if cells:
        print("centring:")
    for name, u, v, w, h in cells:
        line, ok = cell_report(px, name, u, v, w, h)
        print("   " + line)
        bad |= not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

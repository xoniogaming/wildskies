"""Plain pixel tools for painting GUI textures with a script (taken from Fish On!'s tools/artlib.py, without its
region tables): a canvas, ASCII-art stamping, outlines, exact discs, the visible box and centring by it.

    from pixelkit import Cv, rgb, mix, sprite, trimmed, put_centred

Nothing here uses random(): every pixel is placed on purpose and is the same on every run. Alpha is 0 or 255 unless a
painter sets something else on purpose. Keep the regions the HUD code blits in one table next to your painters,
{name: (u, v, w, h)}, and copy the Java constants from it.
"""
import math
import os

from PIL import Image



def rgb(h):
    """'#RRGGBB' or an (r, g, b) tuple -> (r, g, b, 255)."""
    if isinstance(h, str):
        h = h.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    return (h[0], h[1], h[2], 255)


def mix(a, b, k):
    a, b = rgb(a), rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3)) + (255,)


CLEAR = (0, 0, 0, 0)


class Cv:
    """A small RGBA canvas. Alpha is only ever 0 or 255 unless a painter says otherwise (the card burst)."""

    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), rgb(fill) if fill else CLEAR)
        self.px = self.im.load()

    # ---- single pixels and fills (x1/y1 exclusive, like GuiGraphics.fill)
    def p(self, x, y, c):
        if c is not None and 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c if len(c) == 4 else rgb(c)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return CLEAR

    def solid(self, x, y):
        return self.get(x, y)[3] != 0

    def fill(self, x0, y0, x1, y1, c):
        c = rgb(c) if c is not CLEAR else CLEAR
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.px[x, y] = c

    def hl(self, x0, x1, y, c):
        """Row y from x0 to x1 inclusive."""
        self.fill(min(x0, x1), y, max(x0, x1) + 1, y + 1, c)

    def vl(self, x, y0, y1, c):
        """Column x from y0 to y1 inclusive."""
        self.fill(x, min(y0, y1), x + 1, max(y0, y1) + 1, c)

    def dots(self, pts, c):
        for x, y in pts:
            self.p(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.p(int(math.floor(x0 + (x1 - x0) * i / n + 0.5)), int(math.floor(y0 + (y1 - y0) * i / n + 0.5)), c)

    # ---- ASCII art: one character per pixel, '.' and ' ' are skipped
    def art(self, x, y, rows, pal):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in ". ":
                    continue
                if ch == "~":
                    if 0 <= x + i < self.w and 0 <= y + j < self.h:
                        self.px[x + i, y + j] = CLEAR
                    continue
                self.p(x + i, y + j, pal[ch])

    def paste(self, other, x, y, mask=None):
        """Stamps another canvas (its opaque pixels) at x, y."""
        for j in range(other.h):
            for i in range(other.w):
                c = other.px[i, j]
                if c[3] != 0 and (mask is None or mask(i, j)):
                    self.p(x + i, y + j, c)

    def copy(self):
        o = Cv(self.w, self.h)
        o.im = self.im.copy()
        o.px = o.im.load()
        return o

    def crop(self, x, y, w, h):
        o = Cv(w, h)
        o.im = self.im.crop((x, y, x + w, y + h))
        o.px = o.im.load()
        return o

    def flip_h(self):
        o = Cv(self.w, self.h)
        o.im = self.im.transpose(Image.FLIP_LEFT_RIGHT)
        o.px = o.im.load()
        return o

    def flip_v(self):
        o = Cv(self.w, self.h)
        o.im = self.im.transpose(Image.FLIP_TOP_BOTTOM)
        o.px = o.im.load()
        return o

    # ---- shapes
    def disc(self, cx, cy, r, c):
        """Every pixel whose centre is within r of (cx, cy); cx/cy may be on a pixel edge (x.0) or centre (x.5)."""
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                    self.p(x, y, c)

    def ring(self, cx, cy, r0, r1, c):
        for y in range(int(cy - r1 - 1), int(cy + r1 + 2)):
            for x in range(int(cx - r1 - 1), int(cx + r1 + 2)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if r0 < d <= r1:
                    self.p(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.p(x, y, c)

    def outline(self, c, box=None, diag=False, only=None):
        """Puts colour c on every clear pixel that touches an opaque one (4-neighbours, or 8 with diag) inside box
        (x, y, w, h). only(x, y) may restrict where."""
        x0, y0, w, h = box or (0, 0, self.w, self.h)
        add = []
        nb = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (-1, 1), (1, -1), (-1, -1)] if diag else [])
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if self.solid(x, y):
                    continue
                if any(x0 <= x + dx < x0 + w and y0 <= y + dy < y0 + h and self.solid(x + dx, y + dy) for dx, dy in nb):
                    if only is None or only(x, y):
                        add.append((x, y))
        for x, y in add:
            self.p(x, y, c)

    def recolour(self, f, box=None):
        x0, y0, w, h = box or (0, 0, self.w, self.h)
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                c = self.px[x, y]
                if c[3]:
                    self.px[x, y] = f(x, y, c)

    def bbox(self, box=None):
        """Visible box (x0, y0, x1, y1), inclusive, of the opaque pixels inside box, or None."""
        x0, y0, w, h = box or (0, 0, self.w, self.h)
        xs, ys = [], []
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if self.px[x, y][3]:
                    xs.append(x)
                    ys.append(y)
        if not xs:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.im.save(path)


def sprite(rows, pal):
    w = max(len(r) for r in rows)
    cv = Cv(w, len(rows))
    cv.art(0, 0, rows, pal)
    return cv


def trimmed(cv):
    b = cv.bbox()
    return cv.crop(b[0], b[1], b[2] - b[0] + 1, b[3] - b[1] + 1)


def put_centred(dst, cell, spr, name="", want_h=None):
    """Stamps spr centred by its VISIBLE box in cell (x, y, w, h): equal room left/right and top/bottom. The box's
    parity must match the cell's (an odd box cannot centre in an even cell); it raises instead of sitting half a pixel
    off."""
    s = trimmed(spr)
    x, y, w, h = cell
    if (w - s.w) % 2 or (h - s.h) % 2:
        raise ValueError(f"{name}: visible box {s.w}x{s.h} cannot centre in a {w}x{h} cell")
    if s.w > w or s.h > h:
        raise ValueError(f"{name}: {s.w}x{s.h} does not fit {w}x{h}")
    if want_h is not None and s.h != want_h:
        raise ValueError(f"{name}: visible height {s.h}, the HUD expects {want_h}")
    dst.paste(s, x + (w - s.w) // 2, y + (h - s.h) // 2)
    return s.w, s.h


def mirror_rows(rows):
    return [r[::-1] for r in rows]

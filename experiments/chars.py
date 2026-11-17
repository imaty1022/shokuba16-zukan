"""キャラの絵柄違いを描き比べる試作。 python -m experiments.chars
B もち / C 社会人まんが / D ゆる線。A は現行(bot.characters)。
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bot import characters as ch

SS = 3
W = H = 400
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "samples" / "chars"
FONT = str(ROOT / "assets" / "fonts" / "YuseiMagic-Regular.ttf")
WHITE, RED, BLUE, STEEL, GOLD, PINK = "#ffffff", "#e5484d", "#6ec6ff", "#9fb0c3", "#ffd23f", "#f7a8a8"


def spline(pts, n=14):
    """閉じたCatmull-Rom曲線。"""
    out, m = [], len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                    + (-a + 3 * b - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    return out


class P:
    def __init__(self, ink="#2b211c", lw=7):
        self.img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.ink, self.lw = ink, lw

    def _s(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def stroke(self, pts, color=None, w=None, closed=False):
        color, w = color or self.ink, (w or self.lw) * SS
        q = self._s(pts)
        if closed:
            q = q + q[:2]
        self.d.line(q, fill=color, width=int(w), joint="curve")
        for x, y in (q if len(q) < 40 else (q[0], q[-1])):
            self.d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=color)

    def shape(self, pts, fill, smooth=True, lw=None, ink=None):
        pts = spline(pts) if smooth else pts
        self.d.polygon(self._s(pts), fill=fill)
        if lw != 0:
            self.stroke(pts, ink, lw, closed=True)

    def ell(self, cx, cy, rx, ry, fill, lw=None, ink=None, rot=0):
        pts = []
        for i in range(40):
            a = 2 * math.pi * i / 40
            x, y = rx * math.cos(a), ry * math.sin(a)
            r = math.radians(rot)
            pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
        self.shape(pts, fill, smooth=False, lw=lw, ink=ink)

    def dot(self, cx, cy, r, fill=None):
        self.d.ellipse(self._s([(cx - r, cy - r), (cx + r, cy + r)])[0] + self._s([(cx + r, cy + r)])[0], fill=fill or self.ink)

    def arc(self, cx, cy, rx, ry, a0, a1, color=None, w=None):
        n = max(6, int(abs(a1 - a0) / 8))
        self.stroke([(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                      cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)], color, w)

    def done(self, seed=1, amp=1.0):
        return ch.wobble(self.img, seed, amp=amp, wave=60.0)


def bag(p, x, y, s=1.0, lw=None):
    p.arc(x, y - 22 * s, 20 * s, 24 * s, 180, 360, w=lw)
    p.shape([(x - 40 * s, y - 22 * s), (x + 40 * s, y - 22 * s), (x + 44 * s, y + 34 * s), (x - 44 * s, y + 34 * s)],
            "#c98a4b", smooth=False, lw=lw)
    p.stroke([(x - 40 * s, y - 6 * s), (x + 40 * s, y - 6 * s)], w=(lw or p.lw) * 0.7)
    p.ell(x, y - 4 * s, 7 * s, 7 * s, GOLD, lw=(lw or p.lw) * 0.6)


def laptop(p, x, y, s=1.0, lw=None):
    p.shape([(x - 44 * s, y - 50 * s), (x + 44 * s, y - 50 * s), (x + 44 * s, y + 6 * s), (x - 44 * s, y + 6 * s)],
            "#dfe6ee", smooth=False, lw=lw)
    p.shape([(x - 56 * s, y + 6 * s), (x + 56 * s, y + 6 * s), (x + 50 * s, y + 20 * s), (x - 50 * s, y + 20 * s)],
            "#b8c2cf", smooth=False, lw=lw)


def acc(p, kind, cx, y, w, lw=None):
    """頭の小物。cx=頭の中心, y=おでこの高さ, w=頭の半幅。"""
    if kind == "goggles":
        p.stroke([(cx - w * 0.92, y), (cx + w * 0.92, y)], w=(lw or p.lw) * 1.3)
        for dx in (-w * 0.36, w * 0.36):
            p.ell(cx + dx, y, w * 0.27, w * 0.22, STEEL, lw=lw)
            p.arc(cx + dx - w * 0.05, y - w * 0.02, w * 0.12, w * 0.1, 200, 260, WHITE, (lw or p.lw) * 0.6)
    elif kind == "ribbon":
        x = cx - w * 0.55
        p.shape([(x, y), (x - w * 0.36, y - w * 0.26), (x - w * 0.32, y + w * 0.24)], RED, smooth=False, lw=lw)
        p.shape([(x, y), (x + w * 0.36, y - w * 0.26), (x + w * 0.32, y + w * 0.24)], RED, smooth=False, lw=lw)
        p.ell(x, y, w * 0.1, w * 0.1, "#a8324a", lw=lw)
    elif kind == "headband":
        p.shape([(cx + w * 0.86, y), (cx + w * 1.22, y - w * 0.22), (cx + w * 1.14, y + w * 0.06)], RED, smooth=False, lw=lw)
        p.shape([(cx + w * 0.86, y + 2), (cx + w * 1.2, y + w * 0.2), (cx + w * 1.0, y + w * 0.3)], RED, smooth=False, lw=lw)
        p.stroke([(cx - w * 0.9, y), (cx + w * 0.9, y)], w=(lw or p.lw) * 2.6)
        p.stroke([(cx - w * 0.9, y), (cx + w * 0.9, y)], RED, (lw or p.lw) * 1.4)


def lanyard(p, cx, y, s=1.0, lw=None):
    """社員証。職場の話だと一目で分かる記号。"""
    w = (lw or p.lw) * 0.7
    p.stroke([(cx - 30 * s, y), (cx, y + 34 * s), (cx + 30 * s, y)], "#3b82f6", w)
    p.shape([(cx - 17 * s, y + 32 * s), (cx + 17 * s, y + 32 * s), (cx + 17 * s, y + 68 * s), (cx - 17 * s, y + 68 * s)],
            WHITE, smooth=False, lw=w)
    p.dot(cx - 6 * s, y + 46 * s, 5 * s, "#9aa5b1")
    p.stroke([(cx - 10 * s, y + 59 * s), (cx + 10 * s, y + 59 * s)], "#9aa5b1", w * 0.7)


def marks(p, emo, x, y, s=1.0):
    if emo == "shock":
        for i in range(4):
            p.stroke([(x - 21 * s + i * 14 * s, y), (x - 21 * s + i * 14 * s, y + 30 * s)], BLUE, 5)
    elif emo == "angry":
        for a in (0, 90, 180, 270):
            r = math.radians(a + 45)
            cx, cy = x + 28 * s * math.cos(r), y + 28 * s * math.sin(r)
            p.arc(cx, cy, 17 * s, 17 * s, a + 180, a + 270, RED, 7)


# ---------- B: もち ----------
def mochi(fur, emo, accessory, prop=None, walk=False, seed=1):
    p = P(ink="#33261f", lw=8)
    if walk:                                                             # 足: 片方を前に出す
        p.ell(150, 346, 30, 16, fur, rot=-18)
        p.ell(262, 338, 30, 16, fur, rot=-28)
    else:
        p.ell(160, 346, 28, 15, fur)
        p.ell(240, 346, 28, 15, fur)
    p.shape([(118, 160), (128, 86), (186, 122)], fur, smooth=False)      # 耳
    p.shape([(282, 160), (272, 86), (214, 122)], fur, smooth=False)
    p.shape([(134, 136), (137, 108), (160, 124)], PINK, smooth=False, lw=0)
    p.shape([(266, 136), (263, 108), (240, 124)], PINK, smooth=False, lw=0)
    p.ell(84, 286, 18, 24, fur, rot=20)                                  # 手
    p.shape([(92, 332), (72, 236), (108, 148), (200, 116), (292, 148), (328, 236), (308, 332), (200, 348)], fur)
    p.ell(200, 252, 46, 30, "#fff6ea", lw=0)                             # 口まわり
    ey = 222
    for x in (146, 254):
        if emo == "flat":
            p.d.chord([(x - 15) * SS, (ey - 15) * SS, (x + 15) * SS, (ey + 15) * SS], 0, 180, fill=p.ink)
            p.stroke([(x - 20, ey), (x + 20, ey)], w=7)
        elif emo == "shock":
            p.ell(x, ey, 22, 24, WHITE, lw=6)
            p.dot(x, ey, 4)
        else:
            p.dot(x, ey, 11)
            p.dot(x + 4, ey - 4, 3.5, WHITE)
    if emo == "angry":
        p.stroke([(112, 184), (174, 208)], w=12)
        p.stroke([(288, 184), (226, 208)], w=12)
        p.arc(200, 270, 16, 12, 200, 340, w=6)
    elif emo == "shock":
        p.ell(200, 262, 13, 18, p.ink, lw=0)
    elif emo == "flat":
        p.stroke([(190, 262), (210, 262)], w=6)
    else:
        p.arc(190, 252, 10, 10, 20, 160, w=5)
        p.arc(210, 252, 10, 10, 20, 160, w=5)
    p.shape([(193, 240), (207, 240), (200, 249)], "#f08a8a", smooth=False, lw=0)
    for x in (112, 288):
        p.ell(x, 250, 15, 9, "#ffb9b0", lw=0)
    marks(p, emo, *((262, 132) if emo == 'shock' else (318, 110)))
    acc(p, accessory, 200, 172, 96)
    lanyard(p, 200, 286, 0.8)
    if prop == "bag":
        bag(p, 338, 300, 0.95)
        p.ell(300, 276, 24, 15, fur, rot=-10)
    elif prop == "laptop":
        laptop(p, 200, 352, 0.9)
    else:
        p.ell(282, 292, 16, 22, fur, rot=-25)
    out = p.done(seed)
    return out.rotate(7, resample=Image.BICUBIC) if walk else out


# ---------- C: 社会人まんが ----------
def manga(fur, emo, accessory, prop=None, walk=False, seed=1):
    p = P(ink="#1c1c1f", lw=7)
    suit = "#3d4656"
    if walk:                                                             # 大股で歩く
        p.shape([(176, 318), (212, 322), (188, 378), (146, 372)], suit, smooth=False)
        p.shape([(206, 318), (244, 312), (292, 356), (262, 380)], suit, smooth=False)
        p.ell(160, 380, 26, 11, "#1c1c1f", lw=0)
        p.ell(284, 372, 26, 11, "#1c1c1f", lw=0, rot=-30)
    else:
        p.shape([(170, 320), (198, 320), (196, 378), (166, 378)], suit, smooth=False)
        p.shape([(204, 320), (232, 320), (236, 378), (206, 378)], suit, smooth=False)
    p.shape([(154, 238), (246, 238), (258, 330), (144, 330)], WHITE, smooth=False)           # シャツ
    p.shape([(193, 244), (207, 244), (212, 300), (200, 314), (188, 300)], RED, smooth=False, lw=5)   # ネクタイ
    if prop == "bag":
        p.shape([(240, 250), (262, 244), (318, 286), (304, 306)], WHITE, smooth=False)       # 腕
        p.ell(314, 298, 15, 15, fur)
        bag(p, 338, 338, 0.85)
    else:
        p.shape([(240, 250), (262, 246), (280, 304), (258, 312)], WHITE, smooth=False)
        p.ell(270, 312, 15, 15, fur)
    p.shape([(160, 250), (140, 246), (116, 300), (138, 310)], WHITE, smooth=False)
    p.ell(126, 308, 15, 15, fur)
    lanyard(p, 222, 250, 0.62)
    p.shape([(116, 132), (98, 30), (184, 86)], fur, smooth=False)        # 耳
    p.shape([(284, 132), (302, 30), (216, 86)], fur, smooth=False)
    p.shape([(128, 106), (118, 62), (160, 90)], PINK, smooth=False, lw=0)
    p.shape([(272, 106), (282, 62), (240, 90)], PINK, smooth=False, lw=0)
    p.shape([(104, 150), (124, 92), (200, 72), (276, 92), (296, 150), (318, 208), (270, 240), (200, 254),
             (130, 240), (82, 208)], fur)                                # ほっぺの毛が張り出した頭
    p.ell(200, 216, 38, 26, "#fff6ea", lw=0)
    ey = 168
    for sx, x in ((-1, 152), (1, 248)):
        if emo == "flat":                                                # 半目の横目 + 目の下の影
            p.ell(x, ey, 27, 25, WHITE, lw=6)
            p.dot(x + 11, ey + 8, 10)
            p.d.chord([(x - 30) * SS, (ey - 30) * SS, (x + 30) * SS, (ey + 30) * SS], 180, 360, fill=fur)
            p.stroke([(x - 30, ey), (x + 30, ey)], w=9)
            for k in range(3):
                p.stroke([(x - 14 + k * 11, ey + 34), (x - 20 + k * 11, ey + 44)], w=3)
        elif emo == "shock":
            p.ell(x, ey, 30, 32, WHITE, lw=6)
            p.dot(x, ey, 4)
        else:
            p.ell(x, ey, 26, 27, WHITE, lw=6)
            p.dot(x - sx * 3, ey + 3, 11)
            p.dot(x - sx * 3 + 4, ey - 1, 3.5, WHITE)
        if emo == "angry":                                               # つり上がったまぶたで目を切る
            p.shape([(x - sx * 40, ey - 40), (x + sx * 40, ey - 40), (x + sx * 40, ey - 26), (x - sx * 34, ey + 2)],
                    fur, smooth=False, lw=0)
            p.stroke([(x + sx * 34, ey - 24), (x - sx * 30, ey + 2)], w=11)
    if emo == "angry":                                                   # 食いしばり
        p.shape([(176, 216), (224, 216), (220, 238), (180, 238)], WHITE, smooth=False, lw=5)
        for x in (192, 208):
            p.stroke([(x, 218), (x, 236)], w=3)
    elif emo == "shock":
        p.shape([(182, 212), (218, 212), (214, 246), (186, 246)], "#5a1f24", smooth=False, lw=5)
    elif emo == "flat":
        p.stroke([(186, 228), (212, 226)], w=6)
    else:
        p.arc(190, 216, 10, 10, 20, 160, w=5)
        p.arc(210, 216, 10, 10, 20, 160, w=5)
    p.shape([(192, 202), (208, 202), (200, 212)], "#f08a8a", smooth=False, lw=0)
    for sx in (-1, 1):                                                   # ひげ
        p.stroke([(200 + sx * 78, 212), (200 + sx * 116, 204)], w=3)
        p.stroke([(200 + sx * 78, 224), (200 + sx * 114, 230)], w=3)
    marks(p, emo, *((250, 92) if emo == 'shock' else (322, 70)))
    acc(p, accessory, 200, 118, 92)
    if prop == "laptop":
        laptop(p, 200, 356, 0.95)
    out = p.done(seed)
    return out.rotate(6, resample=Image.BICUBIC) if walk else out


# ---------- D: ゆる線 ----------
def yuru(fur, emo, accessory, prop=None, walk=False, seed=1):
    p = P(ink="#3a3a3a", lw=4.5)
    body = "#fffdf8"
    for x, dx in ((172, -14 if walk else 0), (228, 22 if walk else 0)):  # 足は線だけ
        p.stroke([(x, 330), (x + dx, 372), (x + dx + 12, 372)])
    if prop == "bag":
        p.stroke([(252, 232), (292, 258), (318, 262)])
        bag(p, 330, 300, 0.75)
    else:
        p.stroke([(254, 236), (274, 286)])
    p.stroke([(146, 236), (124, 284)])
    p.shape([(132, 132), (136, 84), (176, 108)], fur, smooth=False)
    p.shape([(268, 132), (264, 84), (224, 108)], fur, smooth=False)
    p.shape([(150, 114), (200, 98), (250, 114), (268, 168), (252, 222), (270, 296), (246, 338), (154, 338),
             (130, 296), (148, 222), (132, 168)], body)
    p.d.chord([150 * SS, 96 * SS, 250 * SS, 150 * SS], 180, 360, fill=fur)       # 頭のてっぺんだけ色
    ey = 172
    for x in (178, 222):
        if emo == "flat":
            p.stroke([(x - 9, ey), (x + 9, ey)], w=5)
        else:
            p.dot(x, ey, 6 if emo != "shock" else 4)
        if emo == "angry":
            p.stroke([(x - (x - 200) * 0.7, ey - 12), (x + (x - 200) * 0.5, ey - 22)], w=5)
    if emo == "shock":
        p.ell(200, 196, 7, 9, body, lw=4)
    elif emo == "angry":
        p.arc(200, 200, 10, 7, 200, 340, w=4)
    elif emo == "flat":
        p.stroke([(194, 194), (206, 194)], w=4)
    else:
        p.arc(194, 190, 6, 6, 20, 160, w=4)
        p.arc(206, 190, 6, 6, 20, 160, w=4)
    marks(p, emo, *((240, 62) if emo == 'shock' else (282, 80)), 0.7)
    acc(p, accessory, 200, 134, 62, lw=4)
    lanyard(p, 200, 228, 0.7, lw=5)
    if prop == "laptop":
        laptop(p, 200, 350, 0.8, lw=4)
    out = p.done(seed, amp=1.8)
    return out.rotate(5, resample=Image.BICUBIC) if walk else out


# ================= ゆるかわ路線 =================
YINK = "#5a4436"
CREAM = "#fffaf0"


def yk_face(p, emo, cx, ey, gap=50, s=1.0):
    """顔のパーツを下寄り・小さめに置く。"""
    for sx in (-1, 1):
        x = cx + sx * gap
        if emo == "flat":                                               # 眠そうな線の目
            p.stroke([(x - sx * 13 * s, ey - 1), (x + sx * 13 * s, ey + 4 * s)], w=7 * s)
        elif emo == "shock":                                            # 白目
            p.ell(x, ey, 17 * s, 18 * s, WHITE, lw=5 * s)
        else:
            p.dot(x, ey, 9 * s)
            p.dot(x + 3 * s, ey - 3 * s, 3 * s, WHITE)
        if emo == "angry":
            p.stroke([(x + sx * 17 * s, ey - 27 * s), (x - sx * 13 * s, ey - 15 * s)], w=7 * s)
        p.ell(x + sx * 30 * s, ey + 22 * s, (19 if emo == "angry" else 15) * s, (12 if emo == "angry" else 8) * s,
              "#ff9d94" if emo == "angry" else "#ffc4bb", lw=0)
    my = ey + 20 * s
    if emo == "flat":
        p.stroke([(cx - 6 * s, my), (cx + 6 * s, my)], w=5 * s)
    elif emo == "shock":
        p.ell(cx, my + 4 * s, 7 * s, 10 * s, YINK, lw=0)
    elif emo == "angry":
        p.arc(cx, my + 8 * s, 10 * s, 8 * s, 205, 335, w=5 * s)
    else:
        p.arc(cx - 7 * s, my - 4 * s, 7 * s, 7 * s, 20, 160, w=5 * s)
        p.arc(cx + 7 * s, my - 4 * s, 7 * s, 7 * s, 20, 160, w=5 * s)


def yk_extra(p, emo, x, y):
    if emo == "shock":
        marks(p, "shock", x, y)
        p.shape([(x - 262, y + 60), (x - 250, y + 92), (x - 274, y + 92)], BLUE, lw=0)
    elif emo == "angry":
        marks(p, "angry", x + 6, y + 6, 0.8)
    elif emo == "flat":
        for k in range(3):
            p.dot(x - 14 + k * 17, y + 20, 4.5)


def yk_head(p, fur, earc, emo, accessory):
    p.shape([(98, 132), (112, 58), (170, 92)], earc)
    p.shape([(302, 132), (288, 58), (230, 92)], earc)
    p.shape([(122, 112), (124, 84), (148, 98)], "#ffc4bb", lw=0)
    p.shape([(278, 112), (276, 84), (252, 98)], "#ffc4bb", lw=0)
    p.ell(200, 176, 134, 104, fur)
    yk_face(p, emo, 200, 202)
    acc(p, accessory, 200, 112, 86)
    yk_extra(p, emo, 334, 62)


def shiro(fur, emo, accessory, prop=None, walk=False, seed=1):
    """E 白まる: 白い体に、耳としっぽだけ色。"""
    p = P(ink=YINK, lw=7)
    p.arc(262, 300, 34, 34, -60, 70, w=20)
    p.arc(262, 300, 34, 34, -60, 70, fur, 9)
    p.ell(172 - (10 if walk else 0), 360, 22, 12, CREAM, rot=-15 if walk else 0)
    p.ell(228 + (16 if walk else 0), 356, 22, 12, CREAM, rot=-25 if walk else 0)
    p.ell(200, 306, 60, 56, CREAM)
    p.ell(144, 296, 13, 22, CREAM, rot=28)
    if prop == "bag":
        bag(p, 318, 318, 0.72)
        p.ell(268, 298, 22, 13, CREAM, rot=8)
    else:
        p.ell(256, 296, 13, 22, CREAM, rot=-28)
    yk_head(p, CREAM, fur, emo, accessory)
    lanyard(p, 200, 280, 0.62)
    if prop == "laptop":
        laptop(p, 200, 362, 0.72)
    out = p.done(seed, 1.4)
    return out.rotate(6, resample=Image.BICUBIC) if walk else out


def chibi(fur, emo, accessory, prop=None, walk=False, seed=1):
    """G ちび社員: だぼっとしたシャツとネクタイ。"""
    p = P(ink=YINK, lw=7)
    p.ell(174 - (12 if walk else 0), 362, 22, 12, fur, rot=-15 if walk else 0)
    p.ell(226 + (18 if walk else 0), 358, 22, 12, fur, rot=-25 if walk else 0)
    p.shape([(152, 262), (248, 262), (270, 340), (200, 352), (130, 340)], WHITE)
    p.shape([(194, 276), (206, 276), (210, 312), (200, 324), (190, 312)], "#ff8a80", smooth=False, lw=4)
    p.ell(138, 304, 15, 26, WHITE, rot=24)
    p.ell(128, 328, 10, 10, fur, lw=5)
    if prop == "bag":
        bag(p, 326, 322, 0.72)
        p.ell(270, 300, 26, 15, WHITE, rot=10)
        p.ell(296, 304, 10, 10, fur, lw=5)
    else:
        p.ell(262, 304, 15, 26, WHITE, rot=-24)
        p.ell(272, 328, 10, 10, fur, lw=5)
    yk_head(p, fur, fur, emo, accessory)
    lanyard(p, 226, 282, 0.5)
    if prop == "laptop":
        laptop(p, 200, 364, 0.72)
    out = p.done(seed, 1.4)
    return out.rotate(6, resample=Image.BICUBIC) if walk else out


def tare(fur, emo, accessory, prop=None, walk=False, seed=1):
    """F たれ: 香箱座りのまま生きている。動くときは滑る。"""
    p = P(ink=YINK, lw=7)
    p.arc(338, 268, 36, 50, -80, 40, w=22)
    p.arc(338, 268, 36, 50, -80, 40, fur, 10)
    for x in (112, 176, 250, 308):
        p.ell(x, 350, 20, 11, fur)
    p.shape([(84, 196), (96, 128), (142, 166)], fur)
    p.shape([(152, 170), (180, 110), (212, 162)], fur)
    p.shape([(58, 332), (46, 250), (88, 184), (180, 160), (300, 172), (354, 232), (354, 322), (300, 348), (120, 350)], fur)
    yk_face(p, emo, 150, 262, gap=44)
    acc(p, accessory, 150, 198, 70)
    yk_extra(p, emo, 290, 120)
    if prop == "bag":
        bag(p, 268, 172, 0.62)
        for k in range(3):                                              # すべる線
            p.stroke([(8, 250 + k * 34), (34 - k * 6, 250 + k * 34)], w=5)
    elif prop == "laptop":
        laptop(p, 268, 336, 0.68)
    out = p.done(seed, 1.4)
    return out.transpose(Image.FLIP_LEFT_RIGHT) if False else out


PASTEL = {"ISTP": "#d8b596", "ESFJ": "#bfd3e8", "ENTJ": "#b7b4c8"}
CAST = [("ISTP", "#8a6b57", "flat", "goggles", "bag", True),
        ("ESFJ", "#a9bccd", "shock", "ribbon", "laptop", False),
        ("ENTJ", "#6f7686", "angry", "headband", "laptop", False)]
STYLES = [("B  もち", mochi), ("C  社会人まんが", manga), ("D  ゆる線", yuru)]
YURU = [("E  白まる", shiro), ("F  たれ", tare), ("G  ちび社員", chibi)]


def draw(style, t, size=400):
    fn = dict(B=mochi, C=manga, D=yuru, E=shiro, F=tare, G=chibi)[style]
    _, fur, emo, a, prop, walk = next(c for c in CAST if c[0] == t)
    fur = PASTEL[t] if style in "EFG" else fur
    return fn(fur, emo, a, prop, walk, seed=sum(map(ord, t))).resize((size, size), Image.LANCZOS)


def sheet(rows=None, name="sheet.jpg", pastel=False):
    OUT.mkdir(parents=True, exist_ok=True)
    f = ImageFont.truetype(FONT, 44)
    cell, top = 420, 80
    rows = rows or [("A  現行", None)] + STYLES
    im = Image.new("RGB", (cell * 3 + 40, (cell + top) * len(rows) + 30), "#fffdf5")
    d = ImageDraw.Draw(im)
    for r, (label, fn) in enumerate(rows):
        y = r * (cell + top) + 20
        d.text((30, y + 8), label, font=f, fill="#222")
        d.line((30, y + 66, im.width - 30, y + 66), fill="#222", width=4)
        for c, (t, fur, emo, a, prop, walk) in enumerate(CAST):
            if fn is None:
                one = ch.draw(t, 400, emo, prop)
                one = one.crop((0, 0, min(one.width, 470), 400))
            else:
                one = fn(PASTEL[t] if pastel else fur, emo, a, prop, walk, seed=sum(map(ord, t))).resize((400, 400), Image.LANCZOS)
            im.paste(one, (20 + c * cell, y + top), one)
    im.save(OUT / name, quality=92)


def covers(styles="BCD", name="covers.jpg", first=True):
    """漫画コマの表紙に各絵柄をはめて比べる。"""
    from experiments import design as dz
    crop = dict(B=(40, 60, 360, 380), C=(50, 10, 350, 310), D=(80, 50, 320, 290), E=(40, 30, 360, 350),
                F=(20, 40, 380, 400), G=(40, 30, 360, 350))
    tiles = [dz.d_cover()] if first else []
    for st in styles:
        dz.cat = lambda t, h, e, prop, st=st: draw(st, t, 1200).resize((h, h), Image.LANCZOS)
        dz.draw_head = lambda t, e, size, st=st: draw(st, t, 1200).crop(tuple(v * 3 for v in crop[st])).resize((size, size), Image.LANCZOS)
        im = dz.d_cover()
        im.save(OUT / f"cover_{st}.jpg", quality=92)
        tiles.append(im)
    w, h = tiles[0].size
    n = len(tiles)
    cols = 2 if n == 4 else n
    sh = Image.new("RGB", (w * cols + 20 * (cols + 1), (h + 20) * -(-n // cols) + 20), "#888")
    for i, t in enumerate(tiles):
        sh.paste(t, (20 + (i % cols) * (w + 20), 20 + (i // cols) * (h + 20)))
    sh.resize((sh.width // 2, sh.height // 2), Image.LANCZOS).save(OUT / name, quality=90)


if __name__ == "__main__":
    sheet(YURU, "yuru_sheet.jpg", pastel=True)
    covers("EFG", "yuru_covers.jpg", first=False)

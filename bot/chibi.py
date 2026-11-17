"""ちび社員: ゆるかわ寄りの猫キャラ(16タイプ + 部長)。

見た目のルール:
  頭が大きく、顔のパーツは小さく下寄り。線は焦げ茶で丸い。色は淡い。
  全員シャツと社員証。J = ネクタイあり、P = ノーネクタイ。
  タイプの見分け = 体の色 + 頭の小物。
  E = 口を開けて笑う(normalのとき)。
"""
import math
from functools import lru_cache

from PIL import Image, ImageDraw

from bot import characters as ch

SS = ch.SS
W, H = ch.CW, ch.CH
INK, WHITE, CREAM = "#5a4436", "#ffffff", "#fffaf0"
RED, BLUE, STEEL, GOLD, BLUSH = "#e5484d", "#6ec6ff", "#9fb0c3", "#ffd23f", "#ffc4bb"

FUR = {"INTJ": "#aab4cf", "INTP": "#c9cdd6", "ENTJ": "#b7b4c8", "ENTP": "#f6c98f",
       "INFJ": "#f4efe6", "INFP": "#f3dcc0", "ENFJ": "#f8c6b8", "ENFP": "#fbe3a1",
       "ISTJ": "#b9c6c0", "ISFJ": "#f6e6cf", "ESTJ": "#d3b08c", "ESFJ": "#bfd3e8",
       "ISTP": "#d8b596", "ISFP": "#e3dcf0", "ESTP": "#f4b183", "ESFP": "#f9cfdc",
       "BOSS": "#d9d3c7"}
FOLD = {"INFJ", "ISFJ"}                                   # 折れ耳
POSES = ("", "walk")


def spline(pts, n=14):
    out, m = [], len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                    + (-a + 3 * b - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    return out


class P:
    """太さのそろった丸い線で描くための薄いラッパー(基準座標 480x400)。"""

    def __init__(self, lw=7):
        self.img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.ink, self.lw = INK, lw

    @staticmethod
    def _s(pts):
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
        if fill:
            self.d.polygon(self._s(pts), fill=fill)
        if lw != 0:
            self.stroke(pts, ink, lw, closed=True)

    def ell(self, cx, cy, rx, ry, fill, lw=None, ink=None, rot=0):
        r, pts = math.radians(rot), []
        for i in range(40):
            a = 2 * math.pi * i / 40
            x, y = rx * math.cos(a), ry * math.sin(a)
            pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
        self.shape(pts, fill, smooth=False, lw=lw, ink=ink)

    def dot(self, cx, cy, r, fill=None):
        self.d.ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS), fill=fill or self.ink)

    def arc(self, cx, cy, rx, ry, a0, a1, color=None, w=None):
        n = max(6, int(abs(a1 - a0) / 8))
        self.stroke([(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                      cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)], color, w)

    def star(self, cx, cy, r, fill=GOLD):
        k = r * 0.3
        self.shape([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
                    (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], fill, smooth=False, lw=3)


CX, EY, GAP = 200, 202, 50                                # 顔の中心, 目の高さ, 目の間隔の半分


def accessory(p, t):
    """タイプ固定の頭の小物。顔だけのアイコンでも見分けがつく。"""
    if t == "BOSS":                                       # 太い眉と口ひげ
        for sx in (-1, 1):
            p.stroke([(CX + sx * 72, EY - 34), (CX + sx * 30, EY - 26)], w=12)
            p.ell(CX + sx * 13, EY + 24, 15, 8, INK, lw=0)
    elif t == "INTJ":                                     # 四角い眼鏡
        for sx in (-1, 1):
            x = CX + sx * GAP
            p.shape([(x - 30, EY - 24), (x + 30, EY - 24), (x + 30, EY + 22), (x - 30, EY + 22)], None, smooth=False, lw=5)
        p.stroke([(CX - 20, EY - 4), (CX + 20, EY - 4)], w=5)
    elif t == "INTP":                                     # 丸眼鏡
        for sx in (-1, 1):
            p.ell(CX + sx * GAP, EY, 29, 27, None, lw=5)
        p.stroke([(CX - 21, EY - 2), (CX + 21, EY - 2)], w=5)
    elif t == "ENTJ":                                     # 鉢巻
        y = 112
        p.shape([(CX + 74, y), (CX + 106, y - 20), (CX + 98, y + 6)], RED, smooth=False)
        p.shape([(CX + 74, y + 2), (CX + 104, y + 18), (CX + 86, y + 26)], RED, smooth=False)
        p.stroke([(CX - 78, y), (CX + 78, y)], w=18)
        p.stroke([(CX - 78, y), (CX + 78, y)], RED, 9)
    elif t == "ENTP":                                     # ピアス
        p.ell(300, 104, 10, 10, GOLD, lw=4)
    elif t == "INFJ":                                     # 星のピン
        p.star(118, 124, 20)
    elif t == "INFP":                                     # ヘッドホン
        p.arc(CX, 176, 138, 112, 205, 335, w=18)
        p.arc(CX, 176, 138, 112, 205, 335, "#ff8a80", 9)
        for sx in (-1, 1):
            p.ell(CX + sx * 134, 190, 17, 30, "#ff8a80")
    elif t == "ENFJ":                                     # ハートのバッジ
        x, y = 118, 122
        p.ell(x - 9, y - 4, 11, 11, "#ff6b81", lw=0)
        p.ell(x + 9, y - 4, 11, 11, "#ff6b81", lw=0)
        p.shape([(x - 19, y), (x + 19, y), (x, y + 22)], "#ff6b81", smooth=False, lw=0)
    elif t == "ENFP":                                     # 花
        x, y = 272, 108
        for a in range(0, 360, 72):
            p.ell(x + 15 * math.cos(math.radians(a)), y + 15 * math.sin(math.radians(a)), 11, 11, "#ff8fab", lw=4)
        p.ell(x, y, 8, 8, GOLD, lw=0)
    elif t == "ISTJ":                                     # 耳にペン
        p.stroke([(286, 64), (312, 136)], w=14)
        p.stroke([(286, 64), (312, 136)], GOLD, 7)
        p.dot(284, 58, 6)
    elif t == "ISFJ":                                     # 四つ葉
        x, y = 122, 120
        for dx, dy in ((-9, -9), (9, -9), (-9, 9), (9, 9)):
            p.ell(x + dx, y + dy, 10, 10, "#7bc47f", lw=4)
    elif t == "ESTJ":                                     # ヘッドセット
        p.arc(CX, 176, 138, 112, 205, 335, w=13)
        p.ell(CX - 134, 190, 15, 28, INK, lw=0)
        p.stroke([(CX - 128, 214), (CX - 100, 246), (CX - 60, 246)], w=6)
        p.dot(CX - 58, 246, 10)
    elif t == "ESFJ":                                     # リボン
        x, y = 150, 112
        p.shape([(x, y), (x - 32, y - 22), (x - 28, y + 20)], RED, smooth=False)
        p.shape([(x, y), (x + 32, y - 22), (x + 28, y + 20)], RED, smooth=False)
        p.ell(x, y, 9, 9, "#a8324a")
    elif t == "ISTP":                                     # ゴーグル
        y = 112
        p.stroke([(CX - 80, y), (CX + 80, y)], w=9)
        for sx in (-1, 1):
            p.ell(CX + sx * 31, y, 24, 19, STEEL)
            p.arc(CX + sx * 31 - 5, y - 2, 11, 9, 200, 260, WHITE, 4)
    elif t == "ISFP":                                     # ベレー帽
        p.stroke([(176, 62), (182, 44)], w=8)
        p.ell(172, 84, 78, 27, "#b9485e", rot=-6)
    elif t == "ESTP":                                     # おでこにサングラス
        y = 116
        for sx in (-1, 1):
            p.shape([(CX + sx * 8, y - 16), (CX + sx * 62, y - 16), (CX + sx * 56, y + 14), (CX + sx * 14, y + 14)], INK, lw=4)
        p.stroke([(CX - 76, y - 8), (CX + 76, y - 8)], w=6)
    elif t == "ESFP":                                     # パーティー帽
        p.shape([(206, 14), (164, 84), (246, 80)], "#9b7bff", smooth=False)
        p.stroke([(184, 54), (228, 50)], GOLD, 7)
        p.ell(206, 14, 11, 11, GOLD, lw=4)


def face(p, t, emo):
    """目と口。小さく、下寄りに置く。"""
    big_blush = emo in ("angry", "sparkle")
    for sx in (-1, 1):
        x = CX + sx * GAP
        if emo == "flat":                                               # 眠そうな線の目
            p.stroke([(x - sx * 13, EY - 1), (x + sx * 13, EY + 4)])
        elif emo == "shock":                                            # 白目
            p.ell(x, EY, 17, 18, WHITE, lw=5)
        elif emo == "blank":                                            # 半目の虚無
            p.d.chord([(x - 12) * SS, (EY - 12) * SS, (x + 12) * SS, (EY + 12) * SS], 0, 180, fill=INK)
            p.stroke([(x - 16, EY), (x + 16, EY)])
        elif emo == "sparkle":
            p.dot(x, EY, 15)
            p.dot(x + 5, EY - 6, 5.5, WHITE)
            p.dot(x - 5, EY + 6, 3, WHITE)
        elif emo == "cry":                                              # ぎゅっと閉じて涙
            p.stroke([(x + sx * 13, EY - 8), (x - sx * 8, EY), (x + sx * 13, EY + 8)])
            p.stroke([(x + sx * 4, EY + 16), (x + sx * 4, EY + 58)], BLUE, 11)
        elif emo == "smug":                                             # にんまり
            p.arc(x, EY + 6, 14, 12, 200, 340)
        elif emo == "dead":                                             # ×目
            p.stroke([(x - 11, EY - 11), (x + 11, EY + 11)])
            p.stroke([(x + 11, EY - 11), (x - 11, EY + 11)])
        elif emo == "sleepy":
            p.arc(x, EY - 4, 14, 10, 20, 160)
        else:
            p.dot(x, EY, 6 if emo == "sweat" else 9)
            if emo != "sweat":
                p.dot(x + 3, EY - 3, 3, WHITE)
        if emo == "angry":
            p.stroke([(x + sx * 17, EY - 27), (x - sx * 13, EY - 15)])
        if emo != "cry":
            p.ell(x + sx * 30, EY + 22, 19 if big_blush else 15, 12 if big_blush else 8,
                  "#ff9d94" if emo == "angry" else BLUSH, lw=0)
    my = EY + 20
    if emo in ("flat", "blank"):
        p.stroke([(CX - 6, my), (CX + 6, my)], w=5)
    elif emo == "shock":
        p.ell(CX, my + 4, 7, 10, INK, lw=0)
    elif emo in ("angry", "dead"):
        p.arc(CX, my + 8, 10, 8, 205, 335, w=5)
    elif emo == "sweat":                                                # への字ぎみの波口
        p.stroke([(CX - 12, my + 2), (CX - 4, my - 3), (CX + 4, my + 2), (CX + 12, my - 3)], w=5)
    elif emo in ("sparkle", "cry") or (emo == "normal" and t[0] == "E"):
        p.d.pieslice([(CX - 13) * SS, (my - 14) * SS, (CX + 13) * SS, (my + 14) * SS], 0, 180, fill="#e56b6f")
        p.arc(CX, my, 13, 14, 0, 180, w=5)
        p.stroke([(CX - 13, my), (CX + 13, my)], w=5)
    elif emo == "sleepy":
        p.ell(CX, my + 2, 5, 6, INK, lw=0)
    elif emo == "smug":
        p.arc(CX - 7, my - 4, 7, 7, 20, 160, w=5)
        p.arc(CX + 9, my - 6, 10, 9, 10, 150, w=5)
    else:
        p.arc(CX - 7, my - 4, 7, 7, 20, 160, w=5)
        p.arc(CX + 7, my - 4, 7, 7, 20, 160, w=5)


def effects(p, emo):
    """頭の右上・左に出る漫符。"""
    x, y = 336, 62
    if emo == "shock":
        for i in range(4):
            p.stroke([(x - 21 + i * 14, y), (x - 21 + i * 14, y + 30)], BLUE, 5)
    if emo in ("shock", "sweat"):
        p.shape([(64, 118), (78, 152), (50, 152)], BLUE, lw=0)
    if emo == "angry":
        for a in (0, 90, 180, 270):
            r = math.radians(a + 45)
            p.arc(x + 6 + 22 * math.cos(r), y + 6 + 22 * math.sin(r), 14, 14, a + 180, a + 270, RED, 7)
    elif emo in ("flat", "blank"):
        for k in range(3):
            p.dot(x - 14 + k * 17, y + 20, 4.5)
    elif emo == "sparkle":
        p.star(x + 4, y + 10, 24)
        p.star(64, 110, 16)
    elif emo == "smug":
        p.star(x + 4, y + 10, 22)
    elif emo == "dead":                                                 # 魂が抜ける
        p.shape([(x - 8, y + 34), (x + 20, y + 20), (x + 14, y - 14), (x - 14, y - 8)], WHITE, lw=5)
        p.dot(x - 2, y + 4, 3)
        p.dot(x + 10, y + 2, 3)
    elif emo == "sleepy":
        for k, (dx, s) in enumerate(((0, 13), (22, 9))):
            zx, zy = x - 6 + dx, y + 26 - k * 30
            p.stroke([(zx - s, zy - s), (zx + s, zy - s), (zx - s, zy + s), (zx + s, zy + s)], w=5)


def lanyard(p, cx, y, s=0.5):
    p.stroke([(cx - 30 * s, y), (cx, y + 34 * s), (cx + 30 * s, y)], "#3b82f6", 5)
    p.shape([(cx - 17 * s, y + 32 * s), (cx + 17 * s, y + 32 * s), (cx + 17 * s, y + 68 * s), (cx - 17 * s, y + 68 * s)],
            WHITE, smooth=False, lw=4)
    p.dot(cx - 5 * s, y + 46 * s, 5 * s, "#9aa5b1")
    p.stroke([(cx - 9 * s, y + 59 * s), (cx + 9 * s, y + 59 * s)], "#9aa5b1", 3)


def figure(p, t, emo, hold, walk, head_only=False):
    fur = FUR[t]
    if not head_only:
        p.ell(174 - (12 if walk else 0), 362, 22, 12, fur, rot=-15 if walk else 0)        # 足
        p.ell(226 + (18 if walk else 0), 358, 22, 12, fur, rot=-25 if walk else 0)
        p.shape([(152, 262), (248, 262), (270, 340), (200, 352), (130, 340)], WHITE)      # だぼっとしたシャツ
        if t[3] == "P":                                                                   # ノーネクタイ
            p.stroke([(186, 278), (200, 294), (214, 278)], w=4)
        else:
            p.shape([(194, 276), (206, 276), (210, 312), (200, 324), (190, 312)],
                    "#5b6b8c" if t == "BOSS" else "#ff8a80", smooth=False, lw=4)
        p.ell(138, 304, 15, 26, WHITE, rot=24)
        p.ell(128, 328, 10, 10, fur, lw=5)
        if hold:                                                                          # 小道具を持つ手
            p.ell(272, 296, 28, 15, WHITE, rot=-14)
            p.ell(300, 288, 10, 10, fur, lw=5)
        else:
            p.ell(262, 304, 15, 26, WHITE, rot=-24)
            p.ell(272, 328, 10, 10, fur, lw=5)
    if t in FOLD:
        p.shape([(80, 156), (78, 98), (150, 98)], fur)
        p.shape([(320, 156), (322, 98), (250, 98)], fur)
    else:
        p.shape([(98, 132), (112, 58), (170, 92)], fur)
        p.shape([(302, 132), (288, 58), (230, 92)], fur)
        p.shape([(122, 112), (124, 84), (148, 98)], BLUSH, lw=0)
        p.shape([(278, 112), (276, 84), (252, 98)], BLUSH, lw=0)
    p.ell(CX, 176, 134, 104, fur)
    face(p, t, emo)
    accessory(p, t)
    effects(p, emo)
    if not head_only:
        lanyard(p, 226, 282)


SCENE_PROPS = ("bag", "laptop", "phone")                  # 場面を伝える持ち物だけ残す。タイプ固定の小道具は廃止


def scene_prop(p, prop):
    if prop == "bag":                                     # 通勤かばん(右手)
        x, y, s = 330, 322, 0.72
        p.arc(x, y - 22 * s, 20 * s, 24 * s, 180, 360)
        p.shape([(x - 40 * s, y - 22 * s), (x + 40 * s, y - 22 * s), (x + 44 * s, y + 34 * s), (x - 44 * s, y + 34 * s)],
                "#d9a066", smooth=False)
        p.stroke([(x - 40 * s, y - 6 * s), (x + 40 * s, y - 6 * s)], w=5)
        p.ell(x, y - 4 * s, 6, 6, GOLD, lw=4)
    elif prop == "phone":                                 # スマホ(右手)
        p.shape([(306, 236), (346, 232), (352, 300), (312, 304)], "#4b5563", smooth=False)
        p.shape([(313, 244), (340, 241), (345, 292), (318, 295)], "#e8f1ff", smooth=False, lw=0)
        for k in range(4):
            p.stroke([(319, 252 + k * 10), (338 - (k % 2) * 7, 250 + k * 10)], "#9aa5b1", 3)
    elif prop == "laptop":                                # ノートPC(体の前)
        p.shape([(168, 326), (232, 326), (232, 366), (168, 366)], "#e3e9f1", smooth=False)
        p.shape([(160, 366), (240, 366), (236, 378), (164, 378)], "#bcc6d3", smooth=False)


@lru_cache(maxsize=None)
def _full(t, emo, prop, pose):
    p = P()
    figure(p, t, emo, prop in ("bag", "phone"), pose == "walk")
    scene_prop(p, prop)
    img = ch.wobble(p.img, sum(map(ord, t)), amp=1.4, wave=60.0)
    return img.rotate(6, resample=Image.BICUBIC) if pose == "walk" else img


@lru_cache(maxsize=None)
def _head(t, emo):
    p = P()
    figure(p, t, emo, False, False, head_only=True)
    return ch.wobble(p.img, sum(map(ord, t)), amp=1.4, wave=60.0).crop((40 * SS, 24 * SS, 388 * SS, 300 * SS))


def draw(t, height=400, emotion="normal", prop="", pose=""):
    """全身。propは bag / laptop / phone のみ(それ以外は手ぶら)。pose="walk" で歩く。"""
    im = _full(t, emotion if emotion in ch.EMOTIONS else "normal", prop if prop in SCENE_PROPS else "none", pose)
    return im.resize((round(W * height / H), height), Image.LANCZOS)


def draw_head(t, emotion="normal", size=200):
    """顔だけの正方形(アイコン用)。"""
    im = _head(t, emotion if emotion in ch.EMOTIONS else "normal")
    sq = Image.new("RGBA", (im.width, im.width), (0, 0, 0, 0))
    sq.paste(im, (0, (im.width - im.height) // 2))
    return sq.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":                                 # 一覧を出力: python -m bot.chibi
    from pathlib import Path
    from PIL import ImageFont
    root = Path(__file__).resolve().parent.parent
    f = ImageFont.truetype(str(root / "assets" / "fonts" / "YuseiMagic-Regular.ttf"), 34)
    types = list(ch.COLOR)
    sheet = Image.new("RGB", (4 * 440, 5 * 430), "#fffdf5")
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(types):
        x, y = (i % 4) * 440, (i // 4) * 430
        im = draw(t, 360)
        sheet.paste(im, (x + 10, y + 10), im)
        d.text((x + 200, y + 395), f"{t}  {ch.NICK[t]}", font=f, fill=INK, anchor="mm")
    sheet.save(root / "samples" / "characters.jpg", quality=92)
    sheet = Image.new("RGB", (6 * 300, 2 * 320), "#fffdf5")
    d = ImageDraw.Draw(sheet)
    for k, e in enumerate(ch.EMOTIONS + ["walk"]):
        im = draw("ISTP", 270, "flat", "bag", "walk") if e == "walk" else draw("ESFJ" if k % 2 else "ISTP", 270, e, ("", "laptop", "phone")[k % 3])
        sheet.paste(im, ((k % 6) * 300 - 6, (k // 6) * 320 + 6), im)
        d.text(((k % 6) * 300 + 130, (k // 6) * 320 + 296), e, font=f, fill="#8a7a6c", anchor="mm")
    sheet.save(root / "samples" / "emotions.jpg", quality=92)

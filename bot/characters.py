"""16タイプのオリジナル猫キャラクターをコードで描く。

全員オリジナルの猫。見た目のルール:
  毛並み = タイプごとに違う猫(黒、サバトラ、ハチワレ、茶トラ、白、三毛など)
  E = 口を開けて笑う, I = 目線を落とす
  F = ほっぺが赤い, J = 赤いネクタイ, P = アホ毛
  表情 = ネットミーム風に極端(虚無の見開き、半目の横目、うるうる絶叫など)
  小道具 = タイプごとの仕事道具
"""
import os
import random
from pathlib import Path

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SS = 3                     # スーパーサンプリング倍率
CW, CH = 480, 400          # キャラ1体の基準キャンバス
FONT_DIR = Path(os.environ.get("FONT_DIR", "/usr/share/fonts/opentype/noto"))
DARK, WHITE = "#1f2430", "#ffffff"

TEAMS = [("戦略チーム", "tall", ["INTJ", "INTP", "ENTJ", "ENTP"], ["#1f4e79", "#3a7ca5", "#16425b", "#2f6690"]),
         ("共感チーム", "round", ["INFJ", "INFP", "ENFJ", "ENFP"], ["#e76f51", "#f28482", "#d1495b", "#f4a261"]),
         ("堅実チーム", "square", ["ISTJ", "ISFJ", "ESTJ", "ESFJ"], ["#52796f", "#84a98c", "#386641", "#6a994e"]),
         ("現場チーム", "drop", ["ISTP", "ISFP", "ESTP", "ESFP"], ["#7b5ea7", "#9c89b8", "#5e548e", "#b56576"])]
COLOR = {t: c for _, _, ts, cs in TEAMS for t, c in zip(ts, cs)}
SHAPE = {t: s for _, s, ts, _ in TEAMS for t in ts}
PROP = {"INTJ": ("gantt", "工程表"), "INTP": ("mug", "マグカップ"), "ENTJ": ("megaphone", "メガホン"), "ENTP": ("bulb", "電球"),
        "INFJ": ("plant", "観葉植物"), "INFP": ("headphones", "ヘッドホン"), "ENFJ": ("flag", "旗"), "ENFP": ("cracker", "クラッカー"),
        "ISTJ": ("checklist", "チェックリスト"), "ISFJ": ("tea", "お茶"), "ESTJ": ("stopwatch", "ストップウォッチ"), "ESFJ": ("donut", "差し入れ"),
        "ISTP": ("wrench", "スパナ"), "ISFP": ("palette", "絵筆"), "ESTP": ("can", "エナジー缶"), "ESFP": ("mic", "マイク")}

# 画像でキャラに添える独自の呼び名
NICK = {"INTJ": "戦略オタク", "INTP": "考えこみ屋", "ENTJ": "仕切り隊長", "ENTP": "ひらめき屋",
        "INFJ": "見守り役", "INFP": "夢みる職人", "ENFJ": "まとめ役", "ENFP": "盛り上げ隊",
        "ISTJ": "きっちり番", "ISFJ": "気配り係", "ESTJ": "進行管理人", "ESFJ": "差し入れ係",
        "ISTP": "黙々職人", "ISFP": "感性の人", "ESTP": "即行動派", "ESFP": "ムードメーカー"}
EMOTIONS = ["normal", "sweat", "blank", "sparkle", "flat", "angry", "cry", "smug", "dead", "shock", "sleepy"]
ASSETS = Path(__file__).resolve().parent.parent / "assets" / "chars"
# 一般に知られている通称(キャプションの早見表で使う)
COMMON = {"INTJ": "建築家", "INTP": "論理学者", "ENTJ": "指揮官", "ENTP": "討論者",
          "INFJ": "提唱者", "INFP": "仲介者", "ENFJ": "主人公", "ENFP": "運動家",
          "ISTJ": "管理者", "ISFJ": "擁護者", "ESTJ": "幹部", "ESFJ": "領事",
          "ISTP": "巨匠", "ISFP": "冒険家", "ESTP": "起業家", "ESFP": "エンターテイナー"}


PROPS = ["bag", "laptop", "phone"]                        # 場面を伝える持ち物だけ(タイプ固定の小道具は廃止)


class G:
    """基準座標で描けるようにする薄いラッパー。"""

    def __init__(self, img):
        self.d = ImageDraw.Draw(img)

    @staticmethod
    def s(v):
        return [x * SS for x in v]

    def ell(self, box, fill=None, outline=None, width=0):
        self.d.ellipse(self.s(box), fill=fill, outline=outline, width=width * SS)

    def rrect(self, box, r, fill=None, outline=None, width=0):
        self.d.rounded_rectangle(self.s(box), r * SS, fill=fill, outline=outline, width=width * SS)

    def poly(self, pts, fill):
        self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)

    def line(self, pts, fill, width):
        pts = [(x * SS, y * SS) for x, y in pts]
        self.d.line(pts, fill=fill, width=width * SS, joint="curve")
        r = width * SS / 2
        for x, y in (pts[0], pts[-1]):                     # 丸い端
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def arc(self, box, a0, a1, fill, width):
        self.d.arc(self.s(box), a0, a1, fill=fill, width=width * SS)

    def text(self, xy, s, size, fill):
        f = ImageFont.truetype(str(FONT_DIR / "NotoSansCJK-Black.ttc"), size * SS, index=0)
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor="mm")


# 毛並み: (地の色, 柄, 2色目)。タイプごとに別の猫。
FUR = {"INTJ": ("#2b2d33", "solid", None), "INTP": ("#9aa0a8", "tabby", "#6b7078"),
       "ENTJ": ("#2b2d33", "tuxedo", "#ffffff"), "ENTP": ("#f0a04b", "tabby", "#c9772b"),
       "INFJ": ("#fafafa", "solid", None), "INFP": ("#f3e3c3", "siamese", "#7a5a45"),
       "ENFJ": ("#fafafa", "calico", "#f0a04b"), "ENFP": ("#fafafa", "patch", "#f0a04b"),
       "ISTJ": ("#6f7782", "solid", None), "ISFJ": ("#f1dfc0", "solid", None),
       "ESTJ": ("#a9794f", "tabby", "#7a5232"), "ESFJ": ("#8fa3b8", "tuxedo", "#ffffff"),
       "ISTP": ("#4a3b32", "solid", None), "ISFP": ("#ece7df", "siamese", "#8d8a86"),
       "ESTP": ("#f0a04b", "tuxedo", "#ffffff"), "ESFP": ("#fafafa", "patch", "#8d8a86")}
FUR["BOSS"] = ("#cfc8bb", "tuxedo", "#ffffff")
COLOR["BOSS"] = "#3a3f4b"
NICK = dict(COMMON)                                       # 画像に出す名称は一般に知られた通称にそろえる
NICK["BOSS"] = "部長"
PINK, BLUE = "#f4a6a6", "#6ec6ff"
FOLD = {"INFJ", "ISFJ"}
RED, GOLD, STEEL = "#d1495b", "#ffd23f", "#8d99ae"


def accessory(g, t):
    """タイプ固定の小物。顔アイコンでも見分けがつくようにする。"""
    if t == "BOSS":                                   # 太い眉と口ひげ
        g.line([(128, 132), (186, 142)], DARK, 13)
        g.line([(272, 132), (214, 142)], DARK, 13)
        g.ell((160, 214, 202, 236), fill=DARK)
        g.ell((198, 214, 240, 236), fill=DARK)
    elif t == "INTJ":                                 # 四角い眼鏡
        for x in (158, 242):
            g.rrect((x - 37, 142, x + 37, 210), 10, outline="#dfe3ec", width=6)
        g.line([(195, 172), (205, 172)], "#dfe3ec", 6)
    elif t == "INTP":                                 # 丸眼鏡
        for x in (158, 242):
            g.ell((x - 36, 140, x + 36, 212), outline=DARK, width=6)
        g.line([(194, 174), (206, 174)], DARK, 6)
    elif t == "ENTJ":                                 # 鉢巻
        g.line([(112, 122), (288, 122)], RED, 14)
        g.poly([(288, 114), (322, 96), (316, 128)], RED)
        g.poly([(288, 126), (326, 136), (306, 152)], RED)
    elif t == "ENTP":                                 # ピアス
        g.ell((264, 78, 282, 96), fill=GOLD)
    elif t == "INFP":                                 # ヘッドホン
        g.arc((86, 58, 314, 290), 200, 340, RED, 13)
        g.rrect((74, 150, 110, 216), 14, fill=RED)
        g.rrect((290, 150, 326, 216), 14, fill=RED)
    elif t == "ENFP":                                 # 花
        for dx, dy in ((0, -16), (15, -5), (9, 13), (-9, 13), (-15, -5)):
            g.ell((252 + dx - 11, 96 + dy - 11, 252 + dx + 11, 96 + dy + 11), fill="#ff8fab")
        g.ell((244, 88, 260, 104), fill=GOLD)
    elif t == "ISTJ":                                 # 耳にペン
        g.line([(284, 66), (300, 128)], GOLD, 9)
        g.poly([(280, 52), (288, 52), (284, 66)], DARK)
    elif t == "ESTJ":                                 # ヘッドセット
        g.arc((90, 62, 310, 290), 205, 335, DARK, 11)
        g.rrect((84, 156, 112, 210), 12, fill=DARK)
        g.line([(100, 206), (124, 246), (166, 250)], DARK, 6)
        g.ell((160, 240, 180, 260), fill=DARK)
    elif t == "ESFJ":                                 # リボン
        g.poly([(130, 96), (96, 74), (100, 118)], RED)
        g.poly([(130, 96), (164, 74), (160, 118)], RED)
        g.ell((120, 86, 140, 106), fill="#a8324a")
    elif t == "ISTP":                                 # ゴーグル
        g.line([(108, 116), (292, 116)], DARK, 10)
        for x in (166, 234):
            g.ell((x - 26, 92, x + 26, 140), fill=STEEL, outline=DARK, width=5)
    elif t == "ISFP":                                 # ベレー帽
        g.ell((112, 60, 256, 116), fill="#8d3b4a")
        g.line([(186, 60), (190, 46)], "#8d3b4a", 7)
    elif t == "ESTP":                                 # おでこにサングラス
        for x in (166, 234):
            g.rrect((x - 30, 96, x + 30, 132), 10, fill=DARK)
        g.line([(196, 108), (204, 108)], DARK, 6)
    elif t == "ESFP":                                 # パーティー帽
        g.poly([(206, 40), (166, 100), (244, 96)], "#7c5cff")
        g.line([(186, 70), (228, 68)], GOLD, 7)
        g.ell((196, 30, 216, 50), fill=GOLD)


def lum(h):
    r, g_, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g_ + 0.114 * b


def body(g, t, head_only=False):
    base, pat, sec = FUR[t]
    if not head_only:
        _torso(g, t)
    lc = sec if pat in ("siamese", "calico", "patch") else base
    rc = "#2b2d33" if pat == "calico" else lc
    if t in FOLD:                                                                    # 折れ耳
        g.poly([(104, 140), (112, 84), (186, 100)], lc)
        g.poly([(296, 140), (288, 84), (214, 100)], rc)
        g.poly([(112, 84), (150, 112), (124, 122)], PINK)
        g.poly([(288, 84), (250, 112), (276, 122)], PINK)
    else:
        g.poly([(108, 138), (122, 52), (186, 98)], lc)                               # 耳
        g.poly([(292, 138), (278, 52), (214, 98)], rc)
        g.poly([(128, 112), (133, 78), (160, 100)], PINK)
        g.poly([(272, 112), (267, 78), (240, 100)], PINK)
    g.ell((95, 85, 305, 265), fill=base)                                             # 頭(大きめ)
    if pat == "tabby":
        for x, y1 in ((182, 116), (200, 124), (218, 116)):
            g.line([(x, 94), (x, y1)], sec, 7)
        for y in (172, 190):
            g.line([(106, y), (124, y + 2)], sec, 6)
            g.line([(294, y), (276, y + 2)], sec, 6)
    elif pat == "tuxedo":
        g.ell((155, 190, 245, 262), fill=sec)
    elif pat == "calico":
        g.ell((112, 98, 196, 170), fill=sec)
        g.ell((222, 94, 292, 156), fill="#2b2d33")
    elif pat == "patch":
        g.ell((112, 98, 196, 170), fill=sec)
    elif pat == "siamese":
        g.ell((140, 138, 260, 256), fill=sec)
    if not head_only:
        paw = sec if pat in ("siamese", "tuxedo") else base
        g.ell((146, 330, 196, 354), fill=paw)
        g.ell((204, 330, 254, 354), fill=paw)


def _torso(g, t):
    base, pat, sec = FUR[t]
    g.arc((58, 236, 170, 348), 70, 215, sec if pat == "siamese" else base, 18)      # しっぽ
    g.ell((135, 225, 265, 348), fill=base)                                           # 胴
    if pat == "tuxedo":
        g.ell((172, 250, 228, 332), fill=sec)


def face(g, t, emo="normal", head_only=False):
    base, pat, sec = FUR[t]
    around = sec if pat == "siamese" else base
    ink = DARK if lum(around) > 110 else WHITE
    mink = DARK if pat == "tuxedo" or lum(around) > 110 else WHITE     # 口まわりの線
    ey, xs = 176, (158, 242)

    def eyes(r=25, pr=13, dx=0, dy=0, hi=True):
        for x in xs:
            g.ell((x - r - 4, ey - r - 4, x + r + 4, ey + r + 4), fill=DARK)
            g.ell((x - r, ey - r, x + r, ey + r), fill=WHITE)
            g.ell((x + dx - pr, ey + dy - pr, x + dx + pr, ey + dy + pr), fill=DARK)
            if hi:
                k = pr * 0.34
                g.ell((x + dx + k - k, ey + dy - 2 * k, x + dx + k + k, ey + dy), fill=WHITE)

    def w_mouth():
        g.arc((184, 214, 200, 232), 0, 180, mink, 5)
        g.arc((200, 214, 216, 232), 0, 180, mink, 5)

    for y0, y1 in ((206, 198), (216, 222)):                            # ひげ
        g.line([(126, y0), (90, y1)], ink, 3)
        g.line([(274, y0), (310, y1)], ink, 3)

    if emo == "sweat":
        eyes(pr=8)
        g.arc((186, 226, 214, 246), 180, 360, mink, 5)
        g.ell((284, 96, 306, 128), fill=BLUE)
        g.poly([(295, 74), (285, 110), (305, 110)], BLUE)
    elif emo == "blank":                                               # 半目の虚無(心ここにあらず)
        eyes(r=27, pr=6, dy=6, hi=False)
        for x in xs:
            g.d.chord(G.s((x - 31, ey - 31, x + 31, ey + 31)), 195, 345, fill=DARK)
        g.line([(192, 232), (208, 232)], mink, 5)
    elif emo == "sparkle":
        eyes(r=29, pr=21)
        for x in xs:
            g.ell((x - 14, ey + 4, x - 4, ey + 14), fill=WHITE)
        g.d.pieslice(G.s((178, 216, 222, 260)), 0, 180, fill="#e56b6f")
        for cx, cy, r in ((304, 104, 24), (100, 118, 16)):
            k = r * 0.28
            g.poly([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
                    (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], "#ffd23f")
    elif emo == "flat":                                                # 半目の横目
        eyes(pr=12, dx=10, dy=4, hi=False)
        for x in xs:
            g.d.pieslice(G.s((x - 29, ey - 29, x + 29, ey + 29)), 180, 360, fill=DARK)
        g.line([(188, 232), (212, 232)], mink, 5)
    elif emo == "angry":
        eyes(pr=11)
        g.line([(126, 136), (182, 158)], ink, 10)
        g.line([(274, 136), (218, 158)], ink, 10)
        g.arc((182, 224, 218, 252), 180, 360, mink, 6)
        g.poly([(206, 228), (214, 228), (210, 240)], WHITE)
        for x0, y0, x1, y1 in ((288, 96, 282, 72), (302, 104, 320, 86), (308, 118, 332, 116)):
            g.line([(x0, y0), (x1, y1)], "#e63946", 7)
    elif emo == "cry":                                                 # うるうる絶叫
        eyes(r=29, pr=18)
        for x in xs:
            g.d.pieslice(G.s((x - 29, ey - 29, x + 29, ey + 29)), 25, 155, fill=BLUE)
            g.line([(x, ey + 30), (x, ey + 74)], BLUE, 12)
        g.ell((180, 216, 220, 258), fill=DARK)
        g.ell((189, 238, 211, 256), fill="#e56b6f")
    elif emo == "smug":                                                # ドヤ
        for x in xs:
            g.arc((x - 24, ey - 12, x + 24, ey + 30), 180, 360, ink, 8)
        g.arc((184, 214, 200, 232), 0, 180, mink, 5)
        g.arc((200, 210, 226, 236), 0, 150, mink, 5)
        for cx, cy, r in ((300, 108, 20),):
            k = r * 0.28
            g.poly([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
                    (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], "#ffd23f")
    elif emo == "dead":                                                # ×目
        for x in xs:
            g.line([(x - 17, ey - 17), (x + 17, ey + 17)], ink, 9)
            g.line([(x + 17, ey - 17), (x - 17, ey + 17)], ink, 9)
        g.arc((184, 226, 216, 250), 180, 360, mink, 6)
        for x in (252, 268, 284):
            g.line([(x, 100), (x, 124)], ink, 4)
    elif emo == "shock":                                               # ガーン
        eyes(r=31, pr=4, hi=False)
        g.rrect((184, 218, 216, 258), 10, fill=DARK)
        for x in (150, 166, 182, 218, 234, 250):
            g.line([(x, 98), (x, 126)], BLUE, 5)
    elif emo == "sleepy":                                              # うとうと
        for x in xs:
            g.line([(x - 22, ey + 4), (x + 22, ey + 4)], ink, 9)
        g.ell((193, 222, 207, 238), fill=mink)
        g.text((292, 104), "z", 44, ink)
        g.text((312, 70), "z", 30, ink)
    elif t[0] == "E":
        eyes(pr=15)
        w_mouth()
        g.d.pieslice(G.s((188, 222, 212, 248)), 0, 180, fill="#e56b6f")
    else:
        eyes(pr=12, dx=-6, dy=4)
        w_mouth()
    if emo not in ("cry", "shock"):
        g.poly([(192, 206), (208, 206), (200, 217)], "#f08a8a")        # 鼻

    if t[2] == "F":
        for x in (125, 275):
            g.ell((x - 13, 200, x + 13, 214), fill="#ffb3b3")
    if t[3] == "J" and not head_only:
        g.poly([(189, 262), (211, 262), (200, 275)], "#d1495b")
        g.poly([(200, 273), (189, 298), (200, 310), (211, 298)], "#d1495b")
    elif t[3] == "P":
        g.arc((196, 51, 236, 91), 180, 300, base, 9)


# ---- 小道具(右手の位置 x=300〜460 あたりに描く) ----
def p_phone(g, c):                                    # 長文が並ぶスマホ
    g.rrect((318, 128, 446, 312), 18, fill=DARK)
    g.rrect((328, 146, 436, 296), 8, fill=WHITE)
    g.rrect((334, 152, 430, 276), 8, fill="#dfe9ff")
    for i, w in enumerate((84, 78, 86, 70, 84, 80, 86, 60, 82, 74, 50)):
        g.line([(340, 160 + i * 11), (340 + w, 160 + i * 11)], "#5b6475", 4)
    g.line([(340, 286), (392, 286)], "#c4c9d2", 5)


def p_bag(g, c):                                      # 通勤かばん
    g.arc((352, 176, 420, 250), 180, 360, DARK, 9)
    g.rrect((326, 212, 446, 308), 14, fill="#c98a4b")
    g.rrect((326, 212, 446, 240), 10, fill="#a86f38")
    g.ell((378, 232, 394, 248), fill=GOLD)


def p_laptop(g, c):                                   # 仕事中のノートPC
    g.rrect((322, 168, 446, 262), 10, fill=DARK)
    g.rrect((332, 178, 436, 252), 6, fill="#dfe9ff")
    for i, w in enumerate((80, 60, 72)):
        g.line([(342, 196 + i * 18), (342 + w, 196 + i * 18)], "#5b6475", 5)
    g.rrect((306, 262, 462, 280), 8, fill=STEEL)


def p_gantt(g, c):
    g.rrect((312, 150, 456, 272), 10, fill=WHITE, outline=DARK, width=5)
    for i, (x0, x1, col) in enumerate([(326, 390, "#e76f51"), (356, 430, "#3a7ca5"), (386, 444, "#6a994e")]):
        g.rrect((x0, 172 + i * 30, x1, 190 + i * 30), 6, fill=col)


def p_mug(g, c):
    g.arc((392, 212, 440, 260), 270, 90, DARK, 9)
    g.rrect((330, 196, 410, 280), 10, fill=WHITE, outline=DARK, width=5)
    g.text((372, 148), "？", 54, c)


def p_megaphone(g, c):
    g.poly([(318, 230), (420, 168), (420, 292)], "#e76f51")
    g.rrect((414, 160, 432, 300), 8, fill=DARK)
    for y0, y1 in ((190, 176), (230, 230), (270, 284)):
        g.line([(444, y0), (464, y1)], "#e76f51", 6)


def p_bulb(g, c):
    g.rrect((364, 232, 400, 276), 8, fill=DARK)
    g.ell((334, 150, 430, 246), fill="#ffd23f")
    for x0, y0, x1, y1 in ((382, 136, 382, 116), (322, 168, 306, 156), (442, 168, 458, 156)):
        g.line([(x0, y0), (x1, y1)], "#ffd23f", 6)


def p_plant(g, c):
    g.line([(380, 250), (380, 180)], "#386641", 7)
    g.ell((330, 160, 384, 200), fill="#6a994e")
    g.ell((378, 136, 432, 176), fill="#6a994e")
    g.ell((382, 190, 430, 224), fill="#84a98c")
    g.poly([(334, 244), (426, 244), (412, 304), (348, 304)], "#b5651d")


def p_headphones(g, c):
    g.text((384, 180), "♪", 64, c)
    g.text((428, 244), "♪", 40, c)


def p_flag(g, c):
    g.line([(346, 130), (346, 304)], DARK, 8)
    g.poly([(350, 132), (452, 164), (350, 200)], c)


def p_cracker(g, c):
    g.poly([(322, 300), (372, 216), (410, 250)], "#ffd23f")
    g.line([(340, 270), (366, 290)], "#e76f51", 7)
    for x, y, col in ((392, 190, "#e76f51"), (430, 208, "#3a7ca5"), (416, 150, "#6a994e"),
                      (452, 166, "#ffd23f"), (372, 150, "#9c89b8"), (446, 242, "#f28482")):
        g.ell((x - 9, y - 9, x + 9, y + 9), fill=col)


def p_checklist(g, c):
    g.rrect((320, 152, 444, 304), 10, fill=WHITE, outline=DARK, width=5)
    g.rrect((356, 140, 408, 164), 6, fill=DARK)
    for i in range(3):
        y = 190 + i * 36
        g.line([(338, y), (346, y + 9), (360, y - 9)], c, 6)
        g.line([(376, y), (426, y)], "#c4c9d2", 7)


def p_tea(g, c):
    g.rrect((308, 276, 456, 292), 6, fill="#b5651d")
    for x in (326, 394):
        g.rrect((x, 226, x + 48, 278), 8, fill="#84a98c")
        g.arc((x + 12, 186, x + 36, 218), 90, 270, "#c4c9d2", 5)


def p_stopwatch(g, c):
    g.rrect((368, 150, 392, 176), 5, fill=DARK)
    g.ell((322, 170, 438, 286), fill=WHITE, outline=DARK, width=7)
    g.line([(380, 228), (380, 192)], "#e76f51", 6)
    g.line([(380, 228), (404, 242)], DARK, 6)


def p_donut(g, c):
    g.ell((318, 172, 442, 296), outline="#d9a066", width=38)
    g.arc((318, 172, 442, 296), 180, 360, "#f28482", 38)
    for x, y, col in ((346, 196, WHITE), (382, 184, "#ffd23f"), (416, 200, "#3a7ca5")):
        g.ell((x - 5, y - 5, x + 5, y + 5), fill=col)


def p_wrench(g, c):
    g.line([(340, 296), (402, 204)], "#8d99ae", 22)
    g.ell((376, 150, 448, 222), fill="#8d99ae")
    g.poly([(412, 140), (446, 140), (424, 190), (404, 180)], (0, 0, 0, 0))


def p_palette(g, c):
    g.ell((308, 222, 456, 306), fill="#f1dca7")
    for x, y, col in ((340, 252, "#e76f51"), (376, 242, "#3a7ca5"), (414, 252, "#6a994e"), (390, 280, "#ffd23f")):
        g.ell((x - 11, y - 11, x + 11, y + 11), fill=col)
    g.line([(352, 216), (402, 140)], "#b5651d", 9)
    g.line([(402, 140), (412, 124)], c, 13)


def p_can(g, c):
    g.rrect((344, 176, 420, 304), 12, fill="#ffd23f", outline=DARK, width=5)
    g.poly([(390, 196), (362, 246), (380, 246), (372, 286), (402, 232), (384, 232)], DARK)


def p_mic(g, c):
    g.line([(350, 300), (378, 206)], DARK, 16)
    g.ell((350, 136, 418, 204), fill="#4a5165")
    g.line([(356, 196), (404, 206)], "#ffd23f", 7)
    g.ell((366, 150, 380, 164), fill=WHITE)
    g.text((440, 170), "♪", 52, c)


def wobble(img, seed, amp=1.3, wave=46.0):
    """輪郭をわずかに揺らして、均一なベクター線を手描き寄りにする。"""
    import numpy as np
    a = np.asarray(img)
    h, w = a.shape[:2]
    r = random.Random(seed)
    p1, p2, p3, p4 = (r.uniform(0, 6.28) for _ in range(4))
    k = h / CH                                            # 実解像度あたりの倍率
    ys, xs = np.arange(h), np.arange(w)
    dx = np.rint(amp * k * (np.sin(ys / (wave * k) + p1) + 0.6 * np.sin(ys / (wave * k * 0.37) + p2))).astype(int)
    dy = np.rint(amp * k * (np.sin(xs / (wave * k) + p3) + 0.6 * np.sin(xs / (wave * k * 0.41) + p4))).astype(int)
    out = a[ys[:, None], np.clip(xs[None, :] + dx[:, None], 0, w - 1)]
    out = out[np.clip(ys[:, None] + dy[None, :], 0, h - 1), xs[None, :]]
    return Image.fromarray(out)


INKC, PAPERC = (43, 38, 34), (255, 253, 245)


def handdrawn(img, seed):
    """フラットな絵を手描き風にする: 色の境目=太さの揺れるペン線、塗りは線から少しズレて、色鉛筆のようなムラが乗る。"""
    import numpy as np
    k = img.height / CH                                   # 基準1単位あたりのピクセル数
    a = np.asarray(img).astype(np.int16)
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)

    def smooth_noise(cell):
        low = rng.random((max(2, int(h / (cell * k))), max(2, int(w / (cell * k))))).astype(np.float32)
        return np.asarray(Image.fromarray(low).resize((w, h), Image.BICUBIC))

    # 1) 線: 隣と色が違う場所を拾い、場所によって太さを変える
    diff = np.zeros((h, w), bool)
    dv = np.abs(np.diff(a, axis=0)).sum(axis=-1) > 60
    dh = np.abs(np.diff(a, axis=1)).sum(axis=-1) > 60
    diff[:-1] |= dv
    diff[1:] |= dv
    diff[:, :-1] |= dh
    diff[:, 1:] |= dh
    edge = Image.fromarray((diff * 255).astype(np.uint8))
    thin = np.asarray(edge.filter(ImageFilter.GaussianBlur(0.9 * k))) > 30
    thick = np.asarray(edge.filter(ImageFilter.GaussianBlur(1.5 * k))) > 18
    line = np.where(smooth_noise(30) > 0.68, thick, thin)
    line = Image.fromarray((line * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.35 * k))
    line_l = Image.new("RGBA", img.size, INKC + (0,))
    line_l.putalpha(line.point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(0.2 * k)))

    # 2) 塗り: 少し淡くして色ムラを乗せ、線とは別の揺れ方で少しズラす
    rgb = a[..., :3].astype(np.float32)
    rgb = rgb * 0.9 + 255 * 0.1
    grain = 0.96 + 0.06 * smooth_noise(2)[..., None] + 0.10 * (smooth_noise(34)[..., None] - 0.5)
    rgb = np.clip(rgb * grain, 0, 255)
    fill = Image.fromarray(np.dstack([rgb, a[..., 3:]]).astype(np.uint8), "RGBA")
    fill = wobble(fill, seed + 7, amp=1.5, wave=52.0)
    off = int(round(1.6 * k))
    shifted = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shifted.paste(fill, (off, off))

    # 3) 紙の白: 塗りがズレて空いた所に紙の色が見える
    sil = img.getchannel("A").filter(ImageFilter.GaussianBlur(1.0 * k)).point(lambda v: 255 if v > 60 else 0)
    under = Image.new("RGBA", img.size, PAPERC + (0,))
    under.putalpha(sil)
    out = wobble(under, seed, amp=1.7, wave=40.0)
    out.alpha_composite(shifted)
    out.alpha_composite(wobble(line_l, seed, amp=1.7, wave=40.0))
    return out


@lru_cache(maxsize=None)
def _base(t: str, emotion: str, prop: str = "") -> Image.Image:
    c = COLOR[t]
    img = Image.new("RGBA", (CW * SS, CH * SS), (0, 0, 0, 0))
    g = G(img)
    body(g, t)
    g.line([(252, 292), (326, 250)], FUR[t][0], 18)        # 右前足(小道具を持つ)
    g.line([(150, 288), (120, 306)], FUR[t][0], 18)        # 左前足
    face(g, t, emotion)
    accessory(g, t)
    globals()[f"p_{prop or PROP[t][0]}"](g, c)
    return handdrawn(img, sum(map(ord, t)))


@lru_cache(maxsize=None)
def draw_head(t: str, emotion: str = "normal", size: int = 200) -> Image.Image:
    """顔だけの正方形画像(アイコン・表紙のドアップ用)。大きさに合わせて高解像度で描き直す。"""
    global SS
    old, SS = SS, max(3, -(-size // 240) + 2)
    try:
        img = Image.new("RGBA", (CW * SS, CH * SS), (0, 0, 0, 0))
        g = G(img)
        body(g, t, head_only=True)
        face(g, t, emotion, head_only=True)
        accessory(g, t)
        out = handdrawn(img, sum(map(ord, t))).crop((68 * SS, 18 * SS, 332 * SS, 282 * SS))
    finally:
        SS = old
    return out.resize((size, size), Image.LANCZOS)


CLASSIC = os.environ.get("CHAR_STYLE") == "classic"       # 旧絵柄に戻すとき用
_classic_head = draw_head


def draw_head(t: str, emotion: str = "normal", size: int = 200) -> Image.Image:
    """顔だけの正方形画像。標準は「ちび社員」(bot.chibi)。"""
    if CLASSIC:
        return _classic_head(t, emotion, size)
    from bot import chibi
    return chibi.draw_head(t, emotion, size)


def draw(t: str, height: int = 400, emotion: str = "normal", prop: str = "", pose: str = "") -> Image.Image:
    """タイプtの猫を透過PNG(RGBA)で返す。assets/chars/{TYPE}_{emotion}.png があればそちらを使う。"""
    for name in (f"{t}_{emotion}.png", f"{t}_normal.png"):
        if (ASSETS / name).exists():
            im = Image.open(ASSETS / name).convert("RGBA")
            return im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
    if CLASSIC:
        return _base(t, emotion, prop).resize((round(CW * height / CH), height), Image.LANCZOS)
    from bot import chibi
    return chibi.draw(t, height, emotion, prop, pose)


if __name__ == "__main__":                                 # 16体の一覧と表情一覧を出力
    f = ImageFont.truetype(str(FONT_DIR / "NotoSansCJK-Bold.ttc"), 40, index=0)
    sheet = Image.new("RGB", (4 * 480, 4 * 460), "#f6f1e7")
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(COLOR):
        x, y = (i % 4) * 480, (i // 4) * 460
        ch = draw(t, 380)
        sheet.paste(ch, (x + 12, y + 10), ch)
        d.text((x + 240, y + 420), f"{t}  {NICK[t]}", font=f, fill=COLOR[t], anchor="mm")
    sheet.save("samples/characters.png")
    sheet = Image.new("RGB", (7 * 300, 4 * 300), "#f6f1e7")
    d = ImageDraw.Draw(sheet)
    for r, t in enumerate(["ENTJ", "INFP", "ISTJ", "ESFP"]):
        for k, e in enumerate(EMOTIONS):
            ch = draw(t, 240, e)
            sheet.paste(ch, (k * 300 + 6, r * 300 + 10), ch)
            d.text((k * 300 + 150, r * 300 + 272), e, font=f.font_variant(size=26), fill="#6b7280", anchor="mm")
    sheet.save("samples/emotions.png")

"""同じ論点(定時ぴったりに帰る人)を、6つのデザイン方向で描き分ける試作。各案 表紙/周りの本音/二択 の3枚。
usage: python -m experiments.design"""
import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bot.characters import COLOR, draw as cat, draw_head
from bot.render import H, W, avatar, font as hand, handify, tint
from experiments import talk

ROOT = Path(__file__).resolve().parent.parent
NOTO = Path(os.environ.get("FONT_DIR", "/usr/share/fonts/opentype/noto"))
INK, YEL, RED, BLUE = "#15171c", "#ffe14d", "#ff3b30", "#2f7bff"
HERO = "ISTP"
TITLE = ["18:00:00に", "席を立つ人"]
ASK = "18:03、客先から急ぎの電話。"
QA, QB = "呼び戻す", "朝まで待つ"
ARG_A, ARG_B = "客先を待たせない。今すぐ本人に電話", "定時後は連絡しない。明日9:00に対応"
ARG_AL, ARG_BL = ["客先を待たせない。", "今すぐ本人に電話"], ["定時後は連絡しない。", "明日9:00に対応"]
SERIES = "職場の生きもの図鑑 No.018"
OPT = {"solid": False, "big": False}
VOICES = [("ESFJ", "sweat", "隣の席の人", ["18:05に相談しようと", "思ってたのに、もういない"]),
          ("ENTJ", "angry", "上司", ["先週の18:03の電話、", "私が40分謝りました"]),
          ("ENFP", "sparkle", "後輩", ["先輩が帰るから、", "私も18:10に帰れてます"])]


def crisp(size, weight="Black"):
    return ImageFont.truetype(str(NOTO / f"NotoSansCJK-{weight}.ttc"), size, index=0)


def fitw(d, text, mk, size, max_w):
    while d.textlength(text, font=mk(size)) > max_w and size > 16:
        size -= 2
    return mk(size)


def para(d, lines, mk, size, x, y, fill, max_w, gap=1.25, anchor="la"):
    size = min(size, *(fitw(d, l, mk, size, max_w).size for l in lines))
    f = mk(size)
    for l in lines:
        d.text((x, y), l, font=f, fill=fill, anchor=anchor)
        y += int(size * gap)
    return y


def new(bg):
    img = Image.new("RGB", (W, H), bg)
    return img, ImageDraw.Draw(img)


def paste_rot(img, patch, xy, deg):
    r = patch.rotate(deg, expand=True, resample=Image.BICUBIC)
    img.paste(r, xy, r)


def note(w, h, fill, shadow=True):
    p = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    if shadow:
        d.rectangle((10, 12, w + 14, h + 14), fill=(0, 0, 0, 40))
    d.rectangle((0, 0, w, h), fill=fill)
    return p, d


# ---------- A: 現行(手描きの紙＋場面の絵) ----------
def design_a():
    pages = talk.build(talk.TEIJI3)
    return [pages[0], pages[2], pages[4]], True


# ---------- B: 特大タイポ(黒×黄) ----------
def design_b():
    out = []
    img, d = new(INK)
    d.rectangle((60, 70, 60 + d.textlength("いる、こういう人。", font=crisp(40)) + 48, 140), fill=YEL)
    d.text((84, 78), "いる、こういう人。", font=crisp(40), fill=INK)
    f = fitw(d, "18:00:00", crisp, 300, W - 100)
    d.text((50, 190), "18:00:00", font=f, fill=YEL)
    y = 190 + int(f.size * 1.12)
    d.text((56, y), "に、席を立つ人。", font=fitw(d, "に、席を立つ人。", crisp, 124, W - 120), fill="white")
    d.line([(60, y + 190), (W - 60, y + 190)], fill=YEL, width=8)
    d.ellipse((W - 520, H - 620, W - 40, H - 140), fill=YEL)
    ch = cat(HERO, 440, "flat", "bag")
    img.paste(ch, (W - 520, H - 600), ch)
    d.text((60, H - 420), "ISTPに多い", font=crisp(40, "Bold"), fill="#9aa0a8")
    para(d, ["18:03、客先から", "急ぎの電話。"], crisp, 56, 60, H - 350, "white", 480)
    d.text((60, H - 190), f"{QA}？", font=crisp(72), fill=RED)
    d.text((60, H - 104), f"{QB}？", font=crisp(72), fill="#5aa2ff")
    out.append(img)
    img, d = new(INK)
    d.text((60, 70), "周りの本音", font=crisp(96), fill=YEL)
    for k, (t, e, role, ls) in enumerate(VOICES):
        y = 250 + k * 350
        d.line([(60, y), (W - 60, y)], fill="#3a3f4b", width=4)
        a = avatar(t, e, 170)
        img.paste(a, (60, y + 40), a)
        d.text((260, y + 34), role, font=crisp(40), fill=YEL)
        para(d, ls, crisp, 70, 260, y + 100, "white", W - 320, 1.3)
    out.append(img)
    img, d = new(INK)
    para(d, ["18:03、客先から急ぎの電話。", "あなたが上司なら？"], crisp, 66, 60, 60, "white", W - 120, 1.3)
    for k, (key, col, lbl, arg) in enumerate((("A", RED, QA, ARG_A), ("B", BLUE, QB, ARG_B))):
        y = 270 + k * 450
        d.rectangle((0, y, W, y + 430), fill=col)
        d.text((60, y + 20), key, font=crisp(250), fill="white")
        d.text((300, y + 70), lbl, font=fitw(d, lbl, crisp, 150, W - 360), fill="white")
        d.text((304, y + 290), arg, font=fitw(d, arg, lambda s: crisp(s, "Bold"), 44, W - 360), fill="white")
    d.text((W // 2, H - 96), "A か B、理由を一言でコメント", font=crisp(52), fill=YEL, anchor="mm")
    out.append(img)
    return out, False


# ---------- C: 通知スクショ風(架空のスマホ画面) ----------
def app_icon(d, x, y, col, kind):
    d.rounded_rectangle((x, y, x + 92, y + 92), 24, fill=col)
    if kind == "chat":
        d.rounded_rectangle((x + 20, y + 24, x + 72, y + 60), 14, fill="white")
        d.polygon([(x + 30, y + 58), (x + 28, y + 74), (x + 46, y + 58)], fill="white")
    else:
        d.arc((x + 22, y + 22, x + 76, y + 76), 110, 250, fill="white", width=12)
        d.ellipse((x + 22, y + 56, x + 42, y + 76), fill="white")
        d.ellipse((x + 56, y + 22, x + 76, y + 42), fill="white")


def design_c():
    out = []
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for yy in range(H):                                    # 夕方の壁紙
        k = yy / H
        d.line([(0, yy), (W, yy)], fill=(int(40 + 190 * k), int(50 + 60 * k), int(120 - 30 * k)))
    d.text((70, 44), "18:00", font=crisp(34, "Bold"), fill="white")
    d.rounded_rectangle((W - 150, 50, W - 80, 84), 10, outline="white", width=4)
    d.rectangle((W - 144, 56, W - 100, 78), fill="white")
    d.text((60, 104), "いる、こういう人。", font=crisp(36, "Bold"), fill=YEL)
    d.text((54, 150), "18:00:00に席を立つ人", font=fitw(d, "18:00:00に席を立つ人", crisp, 110, W - 100), fill="white")
    d.text((W // 2, 300), "11月16日 月曜日", font=crisp(38, "Regular"), fill="white", anchor="ma")
    d.text((W // 2, 340), "18:00", font=crisp(230, "Bold"), fill="white", anchor="ma")
    cards = [("ESFJ", "隣の席の人", "いま", ["えっ、もう帰った？", "18:05に相談したかった…"]),
             (None, "客先（不在着信）", "18:03", ["「今日中に確認したい件が", "あります」"])]
    for k, (t, who, when, body) in enumerate(cards):
        y = 650 + k * 250
        d.rounded_rectangle((40, y, W - 40, y + 226), 44, fill=(245, 245, 247))
        if t:
            a = avatar(t, "shock", 130)
            img.paste(a, (62, y + 48), a)
        else:
            app_icon(d, 80, y + 66, "#ff3b30", "call")
        d.text((220, y + 26), who, font=crisp(40), fill=INK)
        d.text((W - 76, y + 32), when, font=crisp(30, "Regular"), fill="#6b7280", anchor="ra")
        para(d, body, lambda z: crisp(z, "Bold"), 46, 220, y + 90, INK, W - 300, 1.3)
    d.rectangle((0, H - 200, W, H), fill=INK)
    d.text((W // 2, H - 150), "18:03、客先から急ぎの電話。あなたが上司なら？", font=fitw(d, "18:03、客先から急ぎの電話。あなたが上司なら？", crisp, 40, W - 80), fill="white", anchor="mm")
    d.text((W // 2, H - 72), f"{QA}？　{QB}？", font=crisp(76), fill=YEL, anchor="mm")
    out.append(img)
    img, d = new("#eef1f5")
    d.rectangle((0, 0, W, 150), fill="white")
    d.text((50, 46), "‹", font=crisp(70, "Regular"), fill=BLUE)
    d.text((W // 2, 44), "定時後の部内チャット", font=crisp(46), fill=INK, anchor="ma")
    d.text((W // 2, 104), "4人（1人は退勤済み）", font=crisp(28, "Regular"), fill="#6b7280", anchor="ma")
    d.text((W // 2, 186), "18:00　ISTP さんが退勤しました", font=crisp(30, "Bold"), fill="#6b7280", anchor="ma")
    for k, (t, e, role, ls) in enumerate(VOICES):
        y = 250 + k * 310
        a = avatar(t, e, 130)
        img.paste(a, (40, y), a)
        d.text((196, y), f"{role}　18:0{5 + k * 2}", font=crisp(30, "Bold"), fill="#6b7280")
        f = crisp(54, "Bold")
        bw = max(d.textlength(l, font=f) for l in ls) + 70
        d.rounded_rectangle((190, y + 46, 190 + bw, y + 46 + 76 * len(ls) + 40), 40, fill="white")
        para(d, ls, lambda s: crisp(s, "Bold"), 54, 224, y + 62, INK, W - 300, 1.4)
    d.text((W // 2, 1190), "既読 3　・　本人の返信は翌朝9:00", font=crisp(34, "Bold"), fill="#6b7280", anchor="mm")
    d.rounded_rectangle((40, 1240, W - 40, 1320), 40, fill="white")
    d.text((80, 1258), "メッセージを入力", font=crisp(34, "Regular"), fill="#9aa0a8")
    out.append(img)
    img, d = new("#eef1f5")
    d.rectangle((0, 0, W, 150), fill="white")
    d.text((W // 2, 50), "アンケート", font=crisp(50), fill=INK, anchor="ma")
    d.rounded_rectangle((40, 200, W - 40, 1130), 50, fill="white")
    para(d, ["18:03、客先から急ぎの電話。", "あなたが上司なら？"], crisp, 62, 86, 250, INK, W - 180, 1.35)
    for k, (key, col, lbl, arg) in enumerate((("A", RED, QA, ARG_A), ("B", BLUE, QB, ARG_B))):
        y = 480 + k * 310
        d.rounded_rectangle((80, y, W - 80, y + 270), 40, fill=col)
        d.ellipse((110, y + 40, 220, y + 150), fill="white")
        d.text((165, y + 92), key, font=crisp(70), fill=col, anchor="mm")
        d.text((250, y + 36), lbl, font=crisp(96), fill="white")
        d.text((252, y + 176), arg, font=fitw(d, arg, lambda s: crisp(s, "Bold"), 40, W - 360), fill="white")
    d.text((W // 2, 1210), "投票はコメントで。A か B、理由を一言", font=crisp(44), fill=INK, anchor="mm")
    out.append(img)
    return out, False


# ---------- D: 漫画コマ ----------
def tone(img, box, step=14, r=3, col=(0, 0, 0)):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    for j, y in enumerate(range(y0, y1, step)):
        for x in range(x0 + (step // 2 if j % 2 else 0), x1, step):
            d.ellipse((x - r, y - r, x + r, y + r), fill=col)


def speed(d, box, n=46, seed=3):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for _ in range(n):
        a = rnd.uniform(0, 6.28)
        r0, r1 = rnd.uniform(0.62, 0.8), 1.5
        d.line([(cx + math.cos(a) * (x1 - x0) / 2 * r0, cy + math.sin(a) * (y1 - y0) / 2 * r0),
                (cx + math.cos(a) * (x1 - x0) * r1, cy + math.sin(a) * (y1 - y0) * r1)], fill=INK, width=rnd.choice((3, 5, 7)))


def balloon(d, box, lines, size=58, tail=None, rect=False):
    if rect:
        d.rounded_rectangle(box, 70, fill="white", outline=INK, width=7)
    else:
        d.ellipse(box, fill="white", outline=INK, width=7)
    if tail:
        d.polygon(tail, fill="white")
        d.line(tail, fill=INK, width=7)
    x0, y0, x1, y1 = box
    f = hand(min(size, *(fitw(d, l, lambda s: hand(s, "Black"), size, (x1 - x0) * (0.9 if rect else 0.82)).size for l in lines)), "Black")
    lh = int(f.size * 1.25)
    y = (y0 + y1) // 2 - lh * len(lines) // 2
    for l in lines:
        d.text(((x0 + x1) // 2, y + lh // 2), l, font=f, fill=INK, anchor="mm")
        y += lh


def panel(img, box, fn):
    """コマ: 枠の中だけに描く。"""
    x0, y0, x1, y1 = box
    sub = Image.new("RGB", (x1 - x0, y1 - y0), "white")
    fn(sub, ImageDraw.Draw(sub))
    img.paste(sub, (x0, y0))
    ImageDraw.Draw(img).rectangle(box, outline=INK, width=10)


def d_cover(band=False, big=False):
    img, d = new("white")
    top = 120 if band else 30

    def p1(s, sd):
        speed(sd, (0, 0, s.width, s.height))
        sd.rounded_rectangle((40, 30, 600, 196), 20, fill=INK)
        sd.text((320, 113), "18:00:00", font=hand(116, "Black"), fill="#ff5a4d", anchor="mm")
        ch = cat(HERO, 540, "flat", "bag", "walk")
        s.paste(ch, (400, s.height - 560), ch)
        sd.text((36, 212), "ガタッ", font=hand(150, "Black"), fill=INK, stroke_width=12, stroke_fill="white")
        balloon(sd, (36, s.height - 250, 400, s.height - 60), ["お先です"], 66)

    def p2(s, sd):
        tone(s, (0, 0, s.width, s.height), 16, 3, (190, 190, 190))
        for k, (t, e) in enumerate((("ESFJ", "shock"), ("ENTJ", "angry"))):
            hd = draw_head(t, e, 280)
            s.paste(hd, (10 + k * 260, s.height - 290), hd)
        sd.text((s.width - 24, 10), "えっ", font=hand(96, "Black"), fill=INK, anchor="ra", stroke_width=10, stroke_fill="white")

    def p3(s, sd):
        sd.rectangle((0, 0, s.width, s.height), fill=YEL)
        sd.text((24, 14), "18:03", font=hand(60, "Black"), fill=INK)
        para(sd, ["客先から", "急ぎの電話"], lambda z: hand(z, "Black"), 44 if s.height < 290 else 54, 24, 84 if s.height < 290 else 96, INK, s.width - 40, 1.2)
        sd.text((s.width // 2, s.height - (44 if s.height < 290 else 60)), "プルルル", font=fitw(sd, "プルルル", lambda z: hand(z, "Black"), 74, s.width - 50), fill=RED, anchor="mm")

    if band:
        d.rectangle((0, 0, W, 100), fill="#2f5d50")
        d.text((40, 24), SERIES, font=hand(46, "Black"), fill="white")
    panel(img, (30, top, W - 30, 770), p1)
    low = 1050 if big else 1100
    panel(img, (30, 790, 620, low), p2)
    panel(img, (640, 790, W - 30, low), p3)
    d.rectangle((0, low + 20, W, H), fill=INK)
    if big:
        d.text((W // 2, 1146), "18:00:00に席を立つ人", font=fitw(d, "18:00:00に席を立つ人", lambda s: hand(s, "Black"), 130, W - 50), fill="white", anchor="mm")
        d.text((W // 2, 1276), f"{QA}？　{QB}？", font=fitw(d, f"{QA}？　{QB}？", lambda s: hand(s, "Black"), 78, W - 80), fill=YEL, anchor="mm")
        return img
    d.text((W // 2, 1186), "18:00:00に席を立つ人", font=fitw(d, "18:00:00に席を立つ人", lambda s: hand(s, "Black"), 120, W - 60), fill="white", anchor="mm")
    d.text((W // 2, 1292), f"あなたが上司なら　{QA}？ {QB}？", font=fitw(d, f"あなたが上司なら　{QA}？ {QB}？", lambda s: hand(s, "Black"), 48, W - 80), fill=YEL, anchor="mm")
    return img


def design_d():
    out = [d_cover()]
    img, d = new("white")
    if False:
        pass
    img, d = new("white")
    for k, (t, e, role, ls) in enumerate(VOICES):
        box = (30, 30 + k * 432, W - 30, 30 + k * 432 + 412)

        def pv(s, sd, t=t, e=e, role=role, ls=ls, k=k):
            if k == 1:
                speed(sd, (0, 0, s.width, s.height), 40, 5)
            else:
                tone(s, (0, 0, s.width, s.height), 18, 3, (205, 205, 205))
            left = k % 2 == 0
            hd = draw_head(t, e, 300)
            s.paste(hd, (0 if left else s.width - 300, 60), hd)
            bx = (290, 40, s.width - 20, 320) if left else (20, 40, s.width - 290, 320)
            balloon(sd, bx, ls, 78, rect=True)
            fs = 48 if OPT["big"] else 36
            cw = sd.textlength(role, font=hand(fs, "Black")) + 40
            cx = 20 if left else s.width - 20 - cw
            sd.rectangle((cx, s.height - fs - 40, cx + cw, s.height - 16), fill=INK)
            sd.text((cx + 20, s.height - fs - 32), role, font=hand(fs, "Black"), fill="white")
            if OPT["big"]:
                tm = f"18:0{5 + k * 2}"
                tw = sd.textlength(tm, font=hand(44, "Black")) + 36
                tx = s.width - 20 - tw if left else 20
                sd.rectangle((tx, s.height - 84, tx + tw, s.height - 16), fill=YEL, outline=INK, width=5)
                sd.text((tx + 18, s.height - 78), tm, font=hand(44, "Black"), fill=INK)

        panel(img, box, pv)
    out.append(img)
    img, d = new("white")
    d.rectangle((30, 30, W - 30, 250), fill=INK)
    para(d, ["18:03、客先から急ぎの電話。", "あなたが上司なら？"], lambda s: hand(s, "Black"), 58, W // 2, 56, "white", W - 140, 1.35, "ma")
    for k, (key, col, lbl, arg, t, e) in enumerate((("A", RED, QA, ARG_A, "ENTJ", "angry"), ("B", BLUE, QB, ARG_B, "ENFP", "sparkle"))):
        def pq(s, sd, key=key, col=col, lbl=lbl, arg=arg, t=t, e=e):
            solid = OPT["solid"]
            sd.rectangle((0, 0, s.width, s.height), fill=col if solid else tint(col, 0.75))
            tone(s, (0, 0, s.width, s.height), 20, 3, tuple(int(c * 0.85) for c in (tint(col, 0.12) if solid else tint(col, 0.6))))
            hd = draw_head(t, e, 380)
            s.paste(hd, ((s.width - 380) // 2, 150), hd)
            sd.text((30, 10), key, font=hand(150, "Black"), fill="white" if solid else col, stroke_width=10, stroke_fill=INK if solid else "white")
            sd.rectangle((0, 560, s.width, 700), fill=INK if solid else col)
            sd.text((s.width // 2, 630), lbl, font=fitw(sd, lbl, lambda z: hand(z, "Black"), 92, s.width - 40), fill="white", anchor="mm")
            para(sd, ARG_AL if key == "A" else ARG_BL, lambda z: hand(z, "Black"), 46 if solid else 42, s.width // 2, 722, "white" if solid else INK, s.width - 40, 1.35, "ma")

        panel(img, (30 + k * 520, 270, 30 + k * 520 + 500, 1150), pq)
    d.ellipse((W // 2 - 80, 640, W // 2 + 80, 800), fill=INK)
    d.text((W // 2, 720), "VS", font=hand(70, "Black"), fill=YEL, anchor="mm")
    d.text((W // 2, 1240), "A か B、理由を一言でコメント", font=hand(52, "Black"), fill=INK, anchor="mm")
    out.append(img)
    return out, True


# ---------- E: 生態図鑑カード ----------
def design_e():
    paper, green = "#f3ecd8", "#2f5d50"
    out = []
    img, d = new(paper)
    d.rectangle((0, 0, W, 120), fill=green)
    d.text((50, 32), "職場の生きもの図鑑", font=hand(52, "Black"), fill="white")
    d.text((W - 50, 40), "No.018", font=hand(44, "Black"), fill=YEL, anchor="ra")
    d.text((50, 150), TITLE[0] + TITLE[1], font=fitw(d, TITLE[0] + TITLE[1], lambda s: hand(s, "Black"), 108, W - 100), fill=INK)
    d.text((54, 276), "分類：ISTPに多い　／　生息地：自席（窓際）", font=hand(32), fill=green)
    d.rounded_rectangle((40, 340, W - 40, 980), 30, outline=green, width=6, fill="#fbf7ea")
    ch = cat(HERO, 560, "flat", "bag")
    img.paste(ch, (200, 380), ch)
    for (tx, ty, px, py, lbl, anchor) in ((66, 372, 430, 565, "目：時計しか見ていない", "la"), (W - 66, 896, 770, 770, "鞄：17:58に準備完了", "ra")):
        f = hand(46, "Black")
        w = d.textlength(lbl, font=f)
        ex = tx + w if anchor == "la" else tx - w
        d.line([(ex, ty + 60), (px, py)], fill=green, width=5)
        d.ellipse((px - 11, py - 11, px + 11, py + 11), fill=green)
        d.text((tx, ty), lbl, font=f, fill=INK, anchor=anchor)
        d.line([(min(tx, ex), ty + 60), (max(tx, ex), ty + 60)], fill=green, width=5)
    rows = [("活動時間", "9:00 〜 18:00:00"), ("鳴き声", "「お先です」"), ("天敵", "18:03の急ぎの電話")]
    for k, (a, b) in enumerate(rows):
        y = 1004 + k * 74
        d.rectangle((40, y, 280, y + 66), fill=green)
        d.text((160, y + 33), a, font=hand(36, "Black"), fill="white", anchor="mm")
        d.rectangle((280, y, W - 40, y + 66), fill="#fbf7ea", outline=green, width=3)
        d.text((304, y + 33), b, font=hand(40, "Black"), fill=INK, anchor="lm")
    d.rectangle((0, 1236, W, H), fill=INK)
    d.text((W // 2, 1270), f"天敵が出た。あなたが上司なら？", font=hand(38, "Black"), fill="white", anchor="mm")
    d.text((W // 2, 1320), f"{QA}？　{QB}？", font=hand(44, "Black"), fill=YEL, anchor="mm")
    out.append(img)
    img, d = new(paper)
    d.rectangle((0, 0, W, 120), fill=green)
    d.text((50, 32), "目撃者の証言", font=hand(52, "Black"), fill="white")
    for k, (t, e, role, ls) in enumerate(VOICES):
        p, pd = note(940, 330, "#fbf7ea")
        pd.rectangle((0, 0, 940, 330), outline=green, width=5)
        a = avatar(t, e, 220)
        p.paste(a, (30, 56), a)
        pd.text((290, 30), f"証言{k + 1}　{role}", font=hand(34, "Black"), fill=green)
        para(pd, ls, lambda s: hand(s, "Black"), 58, 290, 100, INK, 620, 1.35)
        pd.rectangle((380, -6, 560, 24), fill=(255, 225, 77, 200))
        paste_rot(img, p, (56, 160 + k * 380), (-1.5, 1.2, -0.8)[k])
    out.append(img)
    img, d = new(paper)
    d.rectangle((0, 0, W, 120), fill=green)
    d.text((50, 32), "観察者への質問", font=hand(52, "Black"), fill="white")
    para(d, ["18:03、天敵（急ぎの電話）が出現。", "あなたが上司なら？"], lambda s: hand(s, "Black"), 58, 50, 160, INK, W - 100, 1.35)
    for k, (key, col, lbl, arg, t, e) in enumerate((("A", "#d1392b", QA, ARG_A, "ENTJ", "angry"), ("B", "#2f6fd6", QB, ARG_B, "ENFP", "sparkle"))):
        y = 360 + k * 400
        d.rounded_rectangle((40, y, W - 40, y + 360), 30, fill=tint(col, 0.86), outline=col, width=10)
        a = avatar(t, e, 230)
        img.paste(a, (70, y + 100), a)
        d.ellipse((60, y + 30, 170, y + 140), fill=col)
        d.text((115, y + 85), key, font=hand(72, "Black"), fill="white", anchor="mm")
        d.text((340, y + 50), lbl, font=fitw(d, lbl, lambda s: hand(s, "Black"), 120, W - 420), fill=INK)
        d.text((344, y + 236), arg, font=fitw(d, arg, lambda s: hand(s, "Black"), 42, W - 420), fill="#374151")
    d.text((W // 2, 1230), "A か B、理由を一言でコメント", font=hand(52, "Black"), fill=INK, anchor="mm")
    out.append(img)
    return out, True


# ---------- F: 手帳パステル ----------
def grid(d, bg_line="#f0d9d2"):
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=bg_line, width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=bg_line, width=2)


def sticker(t, emo, prop, h):
    """白フチのシール風。"""
    from PIL import ImageFilter
    ch = cat(t, h, emo, prop)
    pad = 24
    base = Image.new("RGBA", (ch.width + pad * 2, ch.height + pad * 2), (0, 0, 0, 0))
    edge = Image.new("L", base.size, 0)
    edge.paste(ch.getchannel("A"), (pad, pad))
    edge = edge.filter(ImageFilter.GaussianBlur(9)).point(lambda v: 255 if v > 20 else 0)
    base.paste(Image.new("RGBA", base.size, "white"), (0, 0), edge)
    base.alpha_composite(ch, (pad, pad))
    return base


def design_f():
    out = []
    img, d = new("#fff5f0")
    grid(d)
    p, pd = note(360, 70, (255, 173, 173, 230), False)
    pd.text((180, 35), "いる、こういう人。", font=hand(36, "Black"), fill="white", anchor="mm")
    paste_rot(img, p, (50, 60), 3)
    p, pd = note(900, 520, "#fff3a8")
    pd.rectangle((330, -10, 570, 34), fill=(180, 220, 255, 210))
    f1 = fitw(pd, TITLE[0], lambda z: hand(z, "Black"), 170, 800)
    pd.text((50, 80), TITLE[0], font=f1, fill=INK)
    w2 = pd.textlength(TITLE[1], font=hand(150, "Black"))
    pd.rectangle((46, 400, 56 + w2, 446), fill="#ffb3c7")
    pd.text((50, 270), TITLE[1], font=hand(150, "Black"), fill=INK)
    paste_rot(img, p, (70, 150), -2)
    st = sticker(HERO, "flat", "bag", 480)
    paste_rot(img, st, (W - st.width - 10, 660), -4)
    p, pd = note(520, 380, "#c9f0e1")
    pd.text((30, 26), "18:03 に客先から", font=hand(40, "Black"), fill=INK)
    pd.text((30, 82), "急ぎの電話。", font=hand(40, "Black"), fill=INK)
    pd.text((30, 150), "あなたが上司なら？", font=hand(44, "Black"), fill="#d1495b")
    pd.text((30, 226), f"□ {QA}", font=hand(50, "Black"), fill=INK)
    pd.text((30, 296), f"□ {QB}", font=hand(50, "Black"), fill=INK)
    paste_rot(img, p, (50, 770), 3)
    d.text((60, 1230), "ISTPに多い", font=hand(36), fill="#9c89b8")
    d.text((W - 60, 1250), "めくって →", font=hand(48, "Black"), fill="#d1495b", anchor="ra")
    out.append(img)
    img, d = new("#fff5f0")
    grid(d)
    d.text((60, 50), "周りの本音", font=hand(84, "Black"), fill=INK)
    d.rectangle((56, 150, 500, 172), fill="#ffb3c7")
    for k, (t, e, role, ls) in enumerate(VOICES):
        col = ("#fff3a8", "#ffd6e0", "#c9f0e1")[k]
        p, pd = note(900, 320, col)
        a = avatar(t, e, 210)
        p.paste(a, (30, 60), a)
        pd.text((270, 30), role, font=hand(36, "Black"), fill="#d1495b")
        para(pd, ls, lambda s: hand(s, "Black"), 58, 270, 96, INK, 600, 1.35)
        pd.rectangle((360, -8, 540, 26), fill=(255, 255, 255, 170))
        paste_rot(img, p, (70 + (k % 2) * 30, 210 + k * 370), (2, -2.5, 1.5)[k])
    out.append(img)
    img, d = new("#fff5f0")
    grid(d)
    para(d, ["18:03、客先から急ぎの電話。", "あなたが上司なら？"], lambda s: hand(s, "Black"), 60, 60, 60, INK, W - 120, 1.35)
    d.rectangle((56, 216, 620, 238), fill="#fff3a8")
    for k, (key, col, lbl, arg) in enumerate((("A", "#ffd6e0", QA, ARG_A), ("B", "#c9f0e1", QB, ARG_B))):
        p, pd = note(920, 380, col)
        pd.rectangle((50, 60, 170, 180), outline=INK, width=8)
        pd.text((110, 120), key, font=hand(90, "Black"), fill=INK, anchor="mm")
        pd.text((210, 50), lbl, font=fitw(pd, lbl, lambda s: hand(s, "Black"), 120, 680), fill=INK)
        pd.text((54, 250), arg, font=fitw(pd, arg, lambda s: hand(s, "Black"), 44, 820), fill="#374151")
        paste_rot(img, p, (60, 290 + k * 430), (-2, 2)[k])
    d.text((W // 2, 1250), "A か B、理由を一言でコメント", font=hand(50, "Black"), fill="#d1495b", anchor="mm")
    out.append(img)
    return out, True


def design_g():
    """表紙=漫画コマ+連載名の帯 / 本文=部内チャット画面 / 締め=特大A・Bに猫の顔"""
    out = [d_cover(band=True)]
    chat = design_c()[0][1]
    dd = ImageDraw.Draw(chat)
    dd.rectangle((0, 0, W, 150), fill="#2f5d50")
    dd.text((40, 22), SERIES, font=hand(46, "Black"), fill="white")
    dd.text((42, 92), "定時後の部内チャット（1人は退勤済み）", font=crisp(32, "Bold"), fill="#cfe3dc")
    out.append(chat)
    img, d = new(INK)
    d.rectangle((0, 0, W, 100), fill="#2f5d50")
    d.text((40, 24), SERIES, font=hand(46, "Black"), fill="white")
    para(d, ["18:03、客先から急ぎの電話。", "あなたが上司なら？"], crisp, 62, 60, 126, "white", W - 120, 1.3)
    for k, (key, col, lbl, arg, t, e) in enumerate((("A", RED, QA, ARG_A, "ENTJ", "angry"), ("B", BLUE, QB, ARG_B, "ENFP", "sparkle"))):
        y = 310 + k * 440
        d.rectangle((0, y, W, y + 410), fill=col)
        hd = draw_head(t, e, 400)
        img.paste(hd, (W - 400, y + 6), hd)
        d.text((40, y - 10), key, font=crisp(250), fill="white")
        d.text((250, y + 60), lbl, font=fitw(d, lbl, crisp, 130, W - 640), fill="white")
        para(d, ARG_AL if key == "A" else ARG_BL, lambda z: crisp(z, "Bold"), 44, 60, y + 270, "white", W - 480, 1.3)
    d.ellipse((W // 2 - 76, 660, W // 2 + 76, 812), fill=INK, outline=YEL, width=8)
    d.text((W // 2, 736), "VS", font=crisp(64), fill=YEL, anchor="mm")
    d.text((W // 2, H - 80), "A か B、理由を一言でコメント", font=crisp(52), fill=YEL, anchor="mm")
    out.append(img)
    return out, False


def design_h():
    """採点役の総意をまとめた仕上げ案: 全ページ漫画の線と書体で統一 + 連載名の帯 + 赤青ベタの締め"""
    OPT.update(solid=True, big=True)
    pages = design_d()[0]
    OPT.update(solid=False, big=False)
    return [d_cover(band=True, big=True), pages[1], pages[2]], True


DESIGNS = {"A": design_a, "B": design_b, "C": design_c, "D": design_d, "E": design_e, "F": design_f, "G": design_g, "H": design_h}
ROUND2 = ["D", "G", "E", "H"]

if __name__ == "__main__":
    out = ROOT / "samples" / "design_top3"
    out.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (3 * 560, len(ROUND2) * 720), "#888")
    for r, k in enumerate(ROUND2):
        pages, rough = DESIGNS[k]()
        for c, im in enumerate(pages):
            if rough and k != "A" or (k == "G" and c == 0):
                im = handify(im, r * 13 + c)
            im.save(out / f"{k}_{c + 1}.jpg", quality=92)
            sheet.paste(im.resize((540, 675)), (c * 560 + 10, r * 720 + 22))
    sheet.save(out / "sheet.jpg", quality=86)

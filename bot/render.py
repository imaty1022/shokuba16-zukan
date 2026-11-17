"""data/today.json からカルーセル画像(1080x1350 JPEG)を作る。

usage: python -m bot.render [入力json] [出力dir]
形式: 架空の社内チャットに16タイプの本音が誤爆する(全6枚)
  01 表紙(顔ドアップ+本音1つ+伏せ字1本) / 02-05 本文(1枚4タイプ) / 06 締め(二択投票+反応TOP3+次回予告)
"""
import json
import os
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bot.characters import COLOR, NICK, draw as draw_char, draw_head

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1350
FONT_DIR = Path(os.environ.get("FONT_DIR", "/usr/share/fonts/opentype/noto"))
BRAND = "職場の16タイプ図鑑"
INK, PAPER, MUTED = "#1f2430", "#f6f1e7", "#6b7280"
DISCLAIMER = "※16タイプ性格分類をもとにした「あるある」ネタです。公式のMBTI®検査とは異なります。"


def tint(hex_color, k=0.8):
    rgb = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    return tuple(round(v + (255 - v) * k) for v in rgb)


HAND_DIR = ROOT / "assets" / "fonts"
HAND_FONTS = {"Black": HAND_DIR / "MochiyPopOne-Regular.ttf",       # 太い見出し用の手書き風
              "Bold": HAND_DIR / "YuseiMagic-Regular.ttf",          # マーカーで書いたような本文用
              "Regular": HAND_DIR / "YuseiMagic-Regular.ttf"}
HAND = all(p.exists() for p in HAND_FONTS.values())                 # フォントが無い・字が無い時は通常の書体に戻す
_cmaps = {}


def _covers(weight, text):
    if weight not in _cmaps:
        from fontTools.ttLib import TTFont
        _cmaps[weight] = set(TTFont(str(HAND_FONTS[weight]), lazy=True).getBestCmap())
    return all(ord(c) in _cmaps[weight] or c.isspace() for c in text)


def font(size, weight="Bold"):
    if HAND:
        return ImageFont.truetype(str(HAND_FONTS[weight]), int(size * (0.9 if weight == "Black" else 1.0)))
    return ImageFont.truetype(str(FONT_DIR / f"NotoSansCJK-{weight}.ttc"), size, index=0)  # index0 = JP


def handify(img, seed):
    """ページ全体をごくわずかに歪ませ、紙のざらつきを乗せる。定規で引いたような直線と均一な面をなくす。"""
    import numpy as np
    rng = np.random.default_rng(seed)
    w2, h2 = W * 2, H * 2
    big = np.asarray(img.resize((w2, h2), Image.LANCZOS))

    def field(amp):
        low = rng.normal(0, 1, (H // 110 + 2, W // 110 + 2)).astype(np.float32)
        return np.asarray(Image.fromarray(low).resize((w2, h2), Image.BICUBIC)) * amp

    ys, xs = np.mgrid[0:h2, 0:w2]
    sx = np.clip(xs + field(2.6), 0, w2 - 1).astype(np.int32)
    sy = np.clip(ys + field(2.6), 0, h2 - 1).astype(np.int32)
    out = Image.fromarray(big[sy, sx]).resize((W, H), Image.LANCZOS)
    a = np.asarray(out).astype(np.float32)
    fine = rng.normal(0, 3.2, (H, W, 1)).astype(np.float32)
    blot = np.asarray(Image.fromarray(rng.normal(0, 1, (H // 40, W // 40)).astype(np.float32)).resize((W, H), Image.BICUBIC))
    a = np.clip(a + fine + blot[..., None] * 2.2, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def wrap(draw, text, fnt, max_w):
    """日本語向けの1文字単位の折り返し(行頭の句読点は前の行に残す)。"""
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=fnt) > max_w and ch not in "、。！？」）…ー":
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    return lines + [cur] if cur else lines


def fit(draw, text, size, weight, max_w, max_lines):
    """max_lines行に収まり、最終行が1文字だけにならない最大のフォントサイズを探す。"""
    while True:
        fnt = font(size, weight)
        lines = wrap(draw, text, fnt, max_w)
        wide = max((draw.textlength(l, font=fnt) for l in lines), default=0) > max_w
        if len(lines) <= max_lines and not wide and not (len(lines) > 1 and len(lines[-1]) <= 1):
            return fnt, balance(draw, lines, fnt, max_w)
        if size <= 16:
            return fnt, lines
        size -= 2


def balance(draw, lines, fnt, max_w):
    """2行の折り返しを、行の長さが近くなる位置に直す(「…とみ/なす」のような切れ方を避ける)。"""
    if len(lines) != 2:
        return lines
    text = "".join(lines)
    mid = (len(text) + 1) // 2
    for cut in (mid, mid + 1, mid - 1):
        a, b = text[:cut], text[cut:]
        if b and b[0] not in "、。！？」）…ー" and a[-1] not in "「（" \
                and draw.textlength(a, font=fnt) <= max_w and draw.textlength(b, font=fnt) <= max_w:
            return [a, b]
    return lines


def text_block(draw, xy, text, fnt, max_w, fill, gap=1.35):
    x, y = xy
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += int(fnt.size * gap)
    return y


BRAND = "職場の16タイプ図鑑"
# カテゴリごとにチャンネル名・帯の色・表紙の地色を変える
SKIN = {"会議": ("定例会議_本音ちゃんねる", "#22283a", "#ff5a4d"), "採用面接": ("面接室_本音ちゃんねる", "#3b2f4a", "#7c5cff"),
        "デスクワーク": ("自席_本音ちゃんねる", "#1f3a3d", "#12b3a6"), "出張": ("出張組_本音ちゃんねる", "#3d2f1f", "#ff8a1f"),
        "チャット・メール": ("未読_本音ちゃんねる", "#2a3350", "#2f7bff"), "1on1・評価": ("面談室_本音ちゃんねる", "#3a2a33", "#ff4f8b"),
        "締切・トラブル": ("炎上中_本音ちゃんねる", "#4a2323", "#e63946"), "オフィスの日常": ("給湯室_本音ちゃんねる", "#2d3a2a", "#3aa655")}
YELLOW, BG = "#ffe14d", "#f4eee1"
REACT = ["わかる", "草", "私だ"]
POST, ITEM, ORDER, REACTS = {}, {}, [], {}


def load(post):
    """描画関数が参照する投稿データをセットする。"""
    global POST, ITEM, ORDER, REACTS, HAND
    POST = post
    if all(p.exists() for p in HAND_FONTS.values()):
        blob = json.dumps(post, ensure_ascii=False)
        HAND = _covers("Black", blob) and _covers("Bold", blob)
        if not HAND:
            print("手書きフォントに無い文字があるため、通常の書体で描画します")
    ITEM = {i["type"]: i for i in post["items"]}
    ORDER = [i["type"] for i in post["items"]]
    rnd = random.Random(post["date"])
    REACTS = {t: (rnd.choice(REACT), rnd.randint(12, 48) * (3 if ITEM[t].get("hot") else 1)) for t in ORDER}


def avatar(t, emo, size):
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(base).ellipse((0, 0, size - 1, size - 1), fill=tint(COLOR[t], 0.5))
    head = draw_head(t, emo, int(size * 0.94))
    base.alpha_composite(head, ((size - head.width) // 2, (size - head.height) // 2 + int(size * 0.03)))
    return base


def header(d, sub, page, total):
    name, color, _ = SKIN[POST["category"]]
    d.rectangle((0, 0, W, 150), fill=color)
    d.text((56, 30), f"# {name}", font=font(44, "Black"), fill="white")
    d.text((58, 96), sub, font=font(27, "Regular"), fill="#c3c9d9")
    bw = d.textlength(BRAND, font=font(24))
    d.rounded_rectangle((W - 56 - bw - 36, 34, W - 56, 82), 24, fill="white")
    d.text((W - 56 - bw - 18, 41), BRAND, font=font(24), fill=color)
    d.text((W - 56, 98), f"{page}/{total}", font=font(27, "Regular"), fill="#c3c9d9", anchor="ra")


def tag(d, xy, t, size=26):
    """4文字コードは小さなタグ扱い。主語は行動の呼び名(role)。"""
    f = font(size, "Black")
    w = d.textlength(t, font=f) + 28
    x, y = xy
    d.rounded_rectangle((x, y, x + w, y + int(size * 1.7)), 10, fill=COLOR[t])
    d.text((x + 14, y + size * 0.85), t, font=f, fill="white", anchor="lm")
    return w


def pill(d, cx, y, label, fnt, fill, color):
    w = d.textlength(label, font=fnt)
    h = int(fnt.size * 1.9)
    d.rounded_rectangle((cx - w / 2 - 40, y, cx + w / 2 + 40, y + h), h // 2, fill=fill)
    d.text((cx, y + h / 2), label, font=fnt, fill=color, anchor="mm")


def clock(t):
    return f"14:03:{ORDER.index(t) * 10 // 16 + 1:02d}"


def cover(total):
    """表紙そのものを2コマのオチにする: 誤爆した本音 → 別の人のツッコミ。"""
    cv = POST["cover"]
    t = cv["type"]
    it = ITEM[t]
    r = next(r for r in POST["replies"] if r["to"] == t)
    col, (chan, dark, vivid) = COLOR[t], SKIN[POST["category"]]
    img = Image.new("RGB", (W, H), vivid)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 104), fill=dark)
    d.text((56, 24), f"# {chan}", font=font(40, "Black"), fill="white")
    bw = d.textlength(BRAND, font=font(24))
    d.rounded_rectangle((W - 56 - bw - 36, 34, W - 56, 82), 24, fill="white")
    d.text((W - 56 - bw - 18, 41), BRAND, font=font(24), fill=dark)
    fnt, ls = fit(d, cv["headline"], 60, "Black", W - 120, 1)
    d.text((60, 128), ls[0], font=fnt, fill="white")
    # 1コマ目: 誤爆した本音
    fnt, ls = fit(d, it["voice"], 124, "Black", W - 230, 2)
    lh = int(fnt.size * 1.16)
    bh = lh * len(ls) + 56
    d.rounded_rectangle((44, 222, W - 110, 222 + bh), 52, fill="white", outline=INK, width=8)
    y = 222 + 24
    for l in ls:
        d.text((76, y), l, font=fnt, fill=INK)
        y += lh
    # 2コマ目: ツッコミ(右寄せ)
    y2 = 222 + bh + 22
    ra = avatar(r["from"], ITEM[r["from"]]["emotion"], 132)
    fr, lr = fit(d, r["text"], 80, "Black", W - 44 - 250, 1)
    rw = d.textlength(lr[0], font=fr) + 70
    d.rounded_rectangle((W - 44 - rw, y2, W - 44, y2 + 150), 48, fill=YELLOW, outline=INK, width=8)
    d.text((W - 44 - rw + 35, y2 + 75), lr[0], font=fr, fill=INK, anchor="lm")
    img.paste(ra, (int(W - 44 - rw - 146), y2 + 10), ra)
    # 発言者の猫と決め文句
    ny = y2 + 176
    size = 1196 - ny
    d.ellipse((-20, 1196 - size, size - 20, 1196), fill=tint(col, 0.35))
    head = draw_head(t, it["emotion"] if it["emotion"] != "smug" else "flat", size)
    img.paste(head, (-10, 1190 - size), head)
    lbl = "全員宛てに誤爆しました"
    lw = d.textlength(lbl, font=font(40, "Black"))
    cx = (size + W - 30) // 2
    d.rounded_rectangle((cx - lw / 2 - 36, 1196 - 150, cx + lw / 2 + 36, 1196 - 66), 42, fill=INK)
    d.text((cx, 1196 - 108), lbl, font=font(40, "Black"), fill=YELLOW, anchor="mm")
    d.text((cx, 1196 - 220), it["role"], font=font(52, "Black"), fill="white", anchor="mm")
    # 下帯: 16人の索引(タイプ名つき)
    d.rectangle((0, 1196, W, H), fill="white")
    d.text((40, 1204), "あなたは、どの人？", font=font(30, "Black"), fill=INK)
    d.text((W - 40, 1208), "タイプ不明なら、役名で探して", font=font(24, "Black"), fill="#d1495b", anchor="ra")
    for k, o in enumerate(ORDER):
        a = avatar(o, ITEM[o]["emotion"], 58)
        img.paste(a, (37 + k * 63, 1250), a)
        d.text((37 + k * 63 + 29, 1322), o, font=font(15, "Black"), fill=COLOR[o], anchor="mm")
    return img


def event(d, text, y0=1252):
    ef = font(38, "Black")
    tw = d.textlength(text, font=ef)
    d.rounded_rectangle(((W - tw) / 2 - 44, y0, (W + tw) / 2 + 44, y0 + 78), 39, fill="#d1495b")
    d.text((W / 2, y0 + 39), text, font=ef, fill="white", anchor="mm")


def hero_page(t, page, total, ev):
    """主役1人で1枚。これだけ送っても成立する。建前の顔 → 本音の全身。"""
    it, col = ITEM[t], COLOR[t]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, POST["cover"]["headline"], page, total)
    fnt, ls = fit(d, it["role"], 92, "Black", W - 130, 1)
    d.text((56, 176), ls[0], font=fnt, fill=INK)
    w = tag(d, (60, 296), t, 30)
    d.text((60 + w + 16, 302), clock(t), font=font(28, "Regular"), fill=MUTED)
    lbl = "これ誰？ → 送って"
    lw = d.textlength(lbl, font=font(30, "Black"))
    d.rounded_rectangle((W - 56 - lw - 44, 292, W - 56, 352), 30, fill=INK)
    d.text((W - 56 - lw - 22, 322), lbl, font=font(30, "Black"), fill=YELLOW, anchor="lm")
    # 建前
    d.rounded_rectangle((44, 384, 444, 850), 36, fill="white")
    f = avatar(t, "smug", 210)
    img.paste(f, (140, 404), f)
    pill(d, 244, 596, "建前", font(26, "Black"), INK, "white")
    fa, la = fit(d, it["action"], 44, "Bold", 350, 4)
    y = 664
    for l in la:
        d.text((244, y), l, font=fa, fill="#1f2937", anchor="ma")
        y += int(fa.size * 1.32)
    d.text((470, 612), "→", font=font(64, "Black"), fill=INK, anchor="mm")
    # 本音(全身)
    d.rounded_rectangle((500, 384, W - 44, 850), 36, fill=tint(col, 0.6))
    emo = it["emotion"] if it["emotion"] != "smug" else "flat"
    ch = draw_char(t, 420, emo, it.get("prop", ""))
    img.paste(ch, (500 + (536 - ch.width) // 2 + 20, 392), ch)
    pill(d, 768, 786, "本音", font(26, "Black"), "#d1495b", "white")
    d.rounded_rectangle((44, 872, W - 150, 1040), 48, fill="white", outline=INK, width=7)
    fv, lv = fit(d, it["voice"], 96, "Black", W - 280, 1)
    d.text((84, 956), lv[0], font=fv, fill=INK, anchor="lm")
    r = next((r for r in POST.get("replies", []) if r["to"] == t), None)
    if r:
        ra = avatar(r["from"], ITEM[r["from"]]["emotion"], 132)
        fr, lr = fit(d, r["text"], 84, "Black", W - 44 - 250, 1)
        rw = d.textlength(lr[0], font=fr) + 70
        d.rounded_rectangle((W - 44 - rw, 1062, W - 44, 1222), 48, fill=YELLOW, outline=INK, width=7)
        d.text((W - 44 - rw + 35, 1142), lr[0], font=fr, fill=INK, anchor="lm")
        img.paste(ra, (int(W - 44 - rw - 146), 1076), ra)
    if ev:
        event(d, ev)
    return img


def list_page(types, page, total, ev=None):
    """主役以外をまとめて見せる一覧。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "同じ10秒、ほかの人たちは", page, total)
    pitch = (H - 190 - (96 if ev else 0)) // len(types)
    for k, t in enumerate(types):
        top = 178 + k * pitch
        it, col = ITEM[t], COLOR[t]
        a = avatar(t, it["emotion"], min(150, pitch - 26))
        img.paste(a, (36, top + 4), a)
        x = 206
        fr, lr = fit(d, it["role"], 42, "Black", 560, 1)
        d.text((x, top - 4), lr[0], font=fr, fill=INK)
        tag(d, (x + d.textlength(lr[0], font=fr) + 16, top + 6), t, 24)
        fa, la = fit(d, "・" + it["action"], 32, "Bold", W - x - 40, 1)
        d.text((x, top + 50), la[0], font=fa, fill="#374151")
        fv, lv = fit(d, it["voice"], 48, "Black", W - x - 110, 1)
        bw = d.textlength(lv[0], font=fv) + 60
        d.rounded_rectangle((x - 4, top + 94, x - 4 + bw, top + 168), 30, fill=tint(col, 0.86), outline=col, width=3)
        d.text((x + 26, top + 131), lv[0], font=fv, fill=INK, anchor="lm")
    if ev:
        event(d, ev)
    return img


def boss_page(page, total):
    """部長だけの1枚。ページをまたいだ伏線のオチ。"""
    dark = SKIN[POST["category"]][1]
    img = Image.new("RGB", (W, H), dark)
    d = ImageDraw.Draw(img)
    header(d, "全員の画面が、止まった", page, total)
    d.text((W // 2, 190), "部長", font=font(120, "Black"), fill="white", anchor="ma")
    d.ellipse((190, 360, 890, 1060), fill="#565d70")
    head = draw_head("BOSS", "flat", 700)
    img.paste(head, (190, 352), head)
    fv, lv = fit(d, POST["boss_line"], 96, "Black", W - 150, 1)
    lh = int(fv.size * 1.2)
    bh = lh * len(lv) + 60
    d.rounded_rectangle((44, 1050, W - 44, 1050 + bh), 48, fill=YELLOW, outline=INK, width=7)
    y = 1050 + 26
    for l in lv:
        d.text((W // 2, y), l, font=fv, fill=INK, anchor="ma")
        y += lh
    return img


def cheat_page(page, total):
    """保存する理由になる実用の1枚。"""
    ch = POST["cheat"]
    img = Image.new("RGB", (W, H), "#fff7cc")
    d = ImageDraw.Draw(img)
    header(d, "保存して、次の会議で使う", page, total)
    d.rounded_rectangle((44, 172, 190, 228), 28, fill="#d1495b")
    d.text((117, 200), "保存用", font=font(30, "Black"), fill="white", anchor="mm")
    ft, lt = fit(d, ch["title"], 44, "Black", W - 260, 1)
    d.text((210, 174), lt[0], font=ft, fill=INK)
    for k, t in enumerate(ORDER):
        x0, y0 = 36 + (k % 2) * 510, 256 + (k // 2) * 132
        d.rounded_rectangle((x0, y0, x0 + 498, y0 + 120), 24, fill="white")
        a = avatar(t, "normal", 96)
        img.paste(a, (x0 + 10, y0 + 12), a)
        w = tag(d, (x0 + 118, y0 + 12), t, 20)
        fr, lr = fit(d, ITEM[t]["role"], 22, "Bold", 498 - 118 - w - 20, 1)
        d.text((x0 + 118 + w + 8, y0 + 14), lr[0], font=fr, fill=MUTED)
        fc, lc = fit(d, f'「{ch["items"][t]}」', 36, "Black", 380, 1)
        d.text((x0 + 106, y0 + 78), lc[0], font=fc, fill=INK, anchor="lm")
    return img


def closing(total):
    q = POST["question"]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "ピン留めされたアンケート", total, total)
    bl = POST.get("boss_last")
    if bl:
        fnt, ls = fit(d, bl, 46, "Black", W - 180, 1)
        tw = d.textlength(ls[0], font=fnt)
        d.rounded_rectangle(((W - tw) / 2 - 44, 176, (W + tw) / 2 + 44, 270), 47, fill="#d1495b")
        d.text((W / 2, 223), ls[0], font=fnt, fill="white", anchor="mm")
    d.rounded_rectangle((44, 300, W - 44, 900), 40, fill="white", outline=INK, width=6)
    fnt, ls = fit(d, q["text"], 84, "Black", W - 170, 1)
    y = 340
    for l in ls:
        d.text((86, y), l, font=fnt, fill=INK)
        y += int(fnt.size * 1.2)
    for k, (key, colr) in enumerate((("a", "#ff5a4d"), ("b", "#2f7bff"))):
        x0 = 86 + k * 462
        d.rounded_rectangle((x0, 470, x0 + 430, 790), 36, fill=colr)
        ct = q[f"cat_{key}"]
        a = avatar(ct, "flat" if ct == "BOSS" else ITEM[ct]["emotion"], 190)
        img.paste(a, (x0 + 120, 486), a)
        d.text((x0 + 60, 530), "AB"[k], font=font(72, "Black"), fill="white", anchor="mm")
        fa, la = fit(d, q[key], 84, "Black", 380, 1)
        d.text((x0 + 215, 728), la[0], font=fa, fill="white", anchor="mm")
    d.text((W // 2, 846), "AかBか、コメントで投票", font=font(44, "Black"), fill=INK, anchor="mm")
    d.rounded_rectangle((44, 930, W - 44, 1090), 30, fill="#dfe3ec")
    d.text((86, 948), "次回予告：明日 20:30 に誤爆予定", font=font(30, "Black"), fill="#d1495b")
    fnt, ls = fit(d, POST["next"], 42, "Bold", W - 180, 2)
    yy = 1004 if len(ls) == 1 else 992
    for l in ls:
        d.text((86, yy), l, font=fnt, fill=INK)
        yy += int(fnt.size * 1.2)
    d.rounded_rectangle((44, 1114, W - 44, 1250), 30, fill=INK)
    d.text((W // 2, 1158), "フォローすると、毎晩20:30に", font=font(34, "Black"), fill="white", anchor="mm")
    d.text((W // 2, 1208), "誰かの本音が誤爆されます", font=font(40, "Black"), fill=YELLOW, anchor="mm")
    text_block(d, (56, 1280), DISCLAIMER, font(23, "Regular"), W - 112, MUTED)
    return img


def plan():
    """ページ構成を決める。主役(hot)は1人1枚、残りは2枚の一覧に分ける。"""
    stars = [t for t in ORDER if ITEM[t].get("hot")]
    rest = [t for t in ORDER if t not in stars]
    half = (len(rest) + 1) // 2
    seq = [("hero", stars[0]), ("list", rest[:half])]
    seq += [("hero", t) for t in stars[1:3]] + [("list", rest[half:])] + [("hero", t) for t in stars[3:]]
    return seq + [("boss", None), ("cheat", None), ("closing", None)]


def render(post, out_dir: Path):
    load(post)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.jpg"):
        old.unlink()
    seq = plan()
    total = len(seq) + 1
    events = iter(POST.get("events", []))
    pages = [cover(total)]
    for n, (kind, arg) in enumerate(seq, start=2):
        if kind == "hero":
            pages.append(hero_page(arg, n, total, next(events, None)))
        elif kind == "list":
            pages.append(list_page(arg, n, total, next(events, None)))
        elif kind == "boss":
            pages.append(boss_page(n, total))
        elif kind == "cheat":
            pages.append(cheat_page(n, total))
        else:
            pages.append(closing(total))
    paths = []
    for n, img in enumerate(pages, start=1):
        p = out_dir / f"{n:02d}.jpg"
        img = handify(img, n * 101 + len(post["date"]))
        img.save(p, "JPEG", quality=92)
        paths.append(p)
    return paths


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "today.json"
    post = json.loads(src.read_text())
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "posts" / post["date"]
    for p in render(post, out):
        print(p)

"""「いる、こういう人。」形式の投稿内容(JSON)から、漫画コマ風のカルーセル画像(1080x1350 x 5枚)を作る。

1 表紙 / 2 周りの本音 / 3 本人の言い分 / 4 二択 / 5 締め
usage: python -m bot.talk_render [post.json] [出力先]
"""
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bot.characters import NICK, draw as cat, draw_head
from bot.render import FONT_DIR, H, W, font as hand, handify, tint

ROOT = Path(__file__).resolve().parent.parent
INK, YEL, RED, BLUE = "#17181c", "#ffe14d", "#ff4d4d", "#2f7bff"
NOTE = "※16タイプ性格分類をもとにした「あるある」です。公式のMBTI®検査とは異なります"


def black(size):
    return hand(size, "Black")


def plain(size):
    return ImageFont.truetype(str(FONT_DIR / "NotoSansCJK-Bold.ttc"), size, index=0)


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


def new(bg="white"):
    img = Image.new("RGB", (W, H), bg)
    return img, ImageDraw.Draw(img)


def tone(img, step=16, r=3, col=(200, 200, 200)):
    """スクリーントーン(網点)。"""
    d = ImageDraw.Draw(img)
    for j, y in enumerate(range(0, img.height, step)):
        for x in range(step // 2 if j % 2 else 0, img.width, step):
            d.ellipse((x - r, y - r, x + r, y + r), fill=col)


def speed(img, n=46, seed=3):
    """集中線。"""
    d, rnd = ImageDraw.Draw(img), random.Random(seed)
    w, h = img.size
    for _ in range(n):
        a = rnd.uniform(0, 6.28)
        r0 = rnd.uniform(0.62, 0.8)
        d.line([(w / 2 + math.cos(a) * w / 2 * r0, h / 2 + math.sin(a) * h / 2 * r0),
                (w / 2 + math.cos(a) * w * 1.5, h / 2 + math.sin(a) * h * 1.5)], fill=INK, width=rnd.choice((3, 5, 7)))


def balloon(d, box, lines, size=58, rect=False):
    if rect:
        d.rounded_rectangle(box, 70, fill="white", outline=INK, width=7)
    else:
        d.ellipse(box, fill="white", outline=INK, width=7)
    x0, y0, x1, y1 = box
    f = black(min(size, *(fitw(d, l, black, size, (x1 - x0) * (0.88 if rect else 0.8)).size for l in lines)))
    lh = int(f.size * 1.3)
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


def label(d, xy, text, size, fill=INK, fg="white", anchor="l", outline=None):
    """黒札。anchor: l=左上基準, r=右上基準。"""
    f = black(size)
    w = int(d.textlength(text, font=f)) + size
    x = xy[0] if anchor == "l" else xy[0] - w
    d.rectangle((x, xy[1], x + w, xy[1] + int(size * 1.6)), fill=fill, outline=outline, width=5)
    d.text((x + w // 2, xy[1] + int(size * 0.8)), text, font=f, fill=fg, anchor="mm")
    return w


def type_name(t):
    return f"{t}・{NICK[t]}"


def header(d, title, post):
    d.rectangle((0, 0, W, 110), fill=INK)
    d.text((40, 55), title, font=black(60), fill="white", anchor="lm")
    name = "".join(post["title_lines"])
    d.text((W - 40, 55), name, font=fitw(d, name, black, 40, 460), fill=YEL, anchor="rm")


# ---------- 1 表紙 ----------
def cover(p):
    img, d = new()
    hero, hv = p["type"], p["hero"]

    def big(s, sd):
        speed(s)
        f = fitw(sd, p["time"], black, 116, 500)
        tw = int(sd.textlength(p["time"], font=f)) + 70
        sd.rounded_rectangle((40, 30, 40 + tw, 196), 20, fill=INK)
        sd.text((40 + tw // 2, 113), p["time"], font=f, fill="#ff5a4d", anchor="mm")
        ch = cat(hero, 560, hv["emotion"], hv.get("prop", "none"), hv.get("pose", ""))
        s.paste(ch, (420, s.height - 575), ch)
        sd.text((36, 212), p["sfx"], font=fitw(sd, p["sfx"], black, 150, 470), fill=INK, stroke_width=12, stroke_fill="white")
        balloon(sd, (36, s.height - 250, 420, s.height - 60), [p["line"]], 66)

    def watch(s, sd):
        tone(s)
        for k, a in enumerate(p["around"][:2]):
            hd = draw_head(a["type"], a["emotion"], 270)
            s.paste(hd, (2 + k * 250, s.height - 262), hd)
        sd.text((s.width - 24, 6), p["react"], font=fitw(sd, p["react"], black, 96, 250), fill=INK, anchor="ra",
                stroke_width=10, stroke_fill="white")

    def event(s, sd):
        ev = p["event"]
        sd.rectangle((0, 0, s.width, s.height), fill=YEL)
        sd.text((24, 14), ev["time"], font=black(60), fill=INK)
        para(sd, ev["lines"], black, 54, 24, 96, INK, s.width - 44, 1.2)
        sd.text((s.width // 2, s.height - 58), ev["sfx"], font=fitw(sd, ev["sfx"], black, 74, s.width - 50), fill=RED, anchor="mm")

    panel(img, (30, 30, W - 30, 760), big)
    panel(img, (30, 780, 620, 1080), watch)
    panel(img, (640, 780, W - 30, 1080), event)
    d.rectangle((0, 1100, W, H), fill=INK)
    label(d, (40, 1116), f"{type_name(hero)}に多い", 34, fill=YEL, fg=INK)
    title = "".join(p["title_lines"])
    d.text((W // 2, 1232), title, font=fitw(d, title, black, 112, W - 70), fill="white", anchor="mm")
    q = f'{p["question"][1].rstrip("？")}　{p["a"]["label"]}？ {p["b"]["label"]}？'
    d.text((W // 2, 1312), q, font=fitw(d, q, black, 48, W - 80), fill=YEL, anchor="mm")
    return img


# ---------- 2 周りの本音 / 3 本人の言い分 ----------
def voice_panel(img, box, t, emo, lines, role, left, style, tag=None):
    def fn(s, sd):
        speed(s, 40, 5) if style == "speed" else tone(s, 18, 3, (205, 205, 205))
        size = min(310, s.height - 70)
        hd = draw_head(t, emo, size)
        s.paste(hd, (0 if left else s.width - size, 26), hd)
        bx = (size - 6, 36, s.width - 22, s.height - 96) if left else (22, 36, s.width - size + 6, s.height - 96)
        balloon(sd, bx, lines, 76, rect=True)
        if left:
            label(sd, (20, s.height - 76), role, 38)
        else:
            label(sd, (s.width - 20, s.height - 76), role, 38, anchor="r")
        if tag:
            if left:
                label(sd, (s.width - 20, s.height - 76), tag, 34, fill=YEL, fg=INK, anchor="r", outline=INK)
            else:
                label(sd, (20, s.height - 76), tag, 34, fill=YEL, fg=INK, outline=INK)
    panel(img, box, fn)


def around(p):
    img, d = new()
    header(d, "周りの本音", p)
    for k, a in enumerate(p["around"]):
        y = 132 + k * 404
        voice_panel(img, (30, y, W - 30, y + 384), a["type"], a["emotion"], a["text"], a["role"], k % 2 == 0,
                    "speed" if k == 1 else "tone")
    return img


def own(p):
    img, d = new()
    hero = p["type"]
    header(d, "本人の言い分", p)
    for k, s in enumerate(p["self"]):
        y = 132 + k * 404
        voice_panel(img, (30, y, W - 30, y + 384), hero, s["emotion"], s["text"], "本人", k % 2 == 1,
                    "tone" if k == 0 else "speed")

    def why(s, sd):
        sd.rectangle((0, 0, s.width, s.height), fill=YEL)
        ch = cat(hero, 330, "normal")
        s.paste(ch, (s.width - 330, s.height - 336), ch)
        label(sd, (26, 24), f"{type_name(hero)}に多いと言われる理由", 34)
        para(sd, p["why"], black, 82, 34, 118, INK, s.width - 380, 1.3)
    panel(img, (30, 940, W - 30, 1320), why)
    return img


# ---------- 4 二択 ----------
def vote(p):
    img, d = new()
    d.rectangle((30, 30, W - 30, 250), fill=INK)
    para(d, p["question"], black, 58, W // 2, 56, "white", W - 140, 1.35, "ma")
    for k, (key, col) in enumerate((("a", RED), ("b", BLUE))):
        c = p[key]

        def fn(s, sd, key=key, col=col, c=c):
            sd.rectangle((0, 0, s.width, s.height), fill=tint(col, 0.75))
            tone(s, 20, 3, tuple(int(v * 0.85) for v in Image.new("RGB", (1, 1), tint(col, 0.6)).getpixel((0, 0))))
            hd = draw_head(c["type"], c["emotion"], 400)
            s.paste(hd, ((s.width - 400) // 2, 150), hd)
            sd.text((30, 10), key.upper(), font=black(150), fill=col, stroke_width=10, stroke_fill="white")
            sd.rectangle((0, 560, s.width, 700), fill=col)
            sd.text((s.width // 2, 630), c["label"], font=fitw(sd, c["label"], black, 92, s.width - 40), fill="white", anchor="mm")
            para(sd, c["arg"], black, 44, s.width // 2, 726, INK, s.width - 40, 1.4, "ma")
        panel(img, (30 + k * 520, 270, 530 + k * 520, 1150), fn)
    d.ellipse((W // 2 - 80, 640, W // 2 + 80, 800), fill=INK)
    d.text((W // 2, 720), "VS", font=black(70), fill=YEL, anchor="mm")
    d.text((W // 2, 1240), "A か B、理由を一言でコメント", font=black(52), fill=INK, anchor="mm")
    return img


# ---------- 5 締め ----------
def closing(p):
    img, d = new()
    hero = p["type"]

    def top(s, sd):
        speed(s, 40, 9)
        ch = cat(hero, 540, p["hero"]["emotion"], p["hero"].get("prop", "none"), p["hero"].get("pose", ""))
        s.paste(ch, (450, s.height - 552), ch)
        balloon(sd, (30, 60, 520, 400), ["あなたの職場にも", "いる？"], 62)
    panel(img, (30, 30, W - 30, 620), top)
    d.rectangle((30, 640, W - 30, 880), fill=INK)
    d.text((W // 2, 722), "コメントで A か B", font=black(88), fill=YEL, anchor="mm")
    d.text((W // 2, 824), "「うちの職場はこう」も聞かせてください", font=fitw(d, "「うちの職場はこう」も聞かせてください", black, 44, W - 140),
           fill="white", anchor="mm")

    def send(s, sd):
        sd.rectangle((0, 0, s.width, s.height), fill=YEL)
        para(sd, ["この人の顔が", "浮かんだら"], black, 54, s.width // 2, 40, INK, s.width - 40, 1.3, "ma")
        sd.text((s.width // 2, s.height - 84), "同僚に送る", font=fitw(sd, "同僚に送る", black, 86, s.width - 50), fill=RED, anchor="mm")

    def nxt(s, sd):
        tone(s)
        label(sd, (22, 22), "次回", 40)
        sd.rectangle((22, 110, s.width - 22, s.height - 26), fill="white", outline=INK, width=6)
        t = p.get("next") or "お楽しみに"
        lines = [t[:len(t) // 2 + len(t) % 2], t[len(t) // 2 + len(t) % 2:]] if len(t) > 8 else [t]
        f = black(min(64, *(fitw(sd, l, black, 64, s.width - 90).size for l in lines)))
        y = (110 + s.height - 26) // 2 - int(f.size * 1.3) * len(lines) // 2
        for l in lines:
            sd.text((s.width // 2, y + int(f.size * 0.65)), l, font=f, fill=INK, anchor="mm")
            y += int(f.size * 1.3)
    panel(img, (30, 900, 530, 1270), send)
    panel(img, (550, 900, W - 30, 1270), nxt)
    d.text((W // 2, 1310), NOTE, font=fitw(d, NOTE, plain, 26, W - 60), fill="#6b7280", anchor="mm")
    return img


def render(post, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.jpg"):
        old.unlink()
    post.setdefault("title_lines", post["title"] if isinstance(post["title"], list) else [post["title"]])
    paths = []
    for n, fn in enumerate((cover, around, own, vote, closing), start=1):
        path = out_dir / f"{n:02d}.jpg"
        handify(fn(post), n * 13).save(path, quality=92)
        paths.append(path)
    return paths


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "today.json"
    post = json.loads(src.read_text())
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "posts" / post["date"]
    for path in render(post, out):
        print(path)

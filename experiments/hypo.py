"""仮説3つの試作。 usage: python -m experiments.hypo
H1 1投稿1ネタの3コマ劇場 / H2 2人の関係(送り先を内蔵) / H3 4択診断(読者参加)"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

from bot import render as R
from bot.characters import COLOR, draw as cat, draw_head
from bot.render import BG, H, INK, MUTED, W, YELLOW, avatar, fit, font, handify, tint

ROOT = Path(__file__).resolve().parent.parent
POST = json.loads((ROOT / "samples" / "all16.json").read_text())
R.load(POST)
IT = R.ITEM
DARK, RED = "#22283a", "#d1495b"


def base(bg, label, page, total):
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 104), fill=DARK)
    d.text((56, 24), label, font=font(40, "Black"), fill="white")
    d.text((W - 56, 34), f"{page}/{total}", font=font(30, "Regular"), fill="#c3c9d9", anchor="ra")
    return img, d


def bubble(d, box, text, fill, size=110, lines=2, tail=None):
    d.rounded_rectangle(box, 52, fill=fill, outline=INK, width=8)
    if tail:
        d.polygon(tail, fill=fill)
        d.line([tail[0], tail[1], tail[2]], fill=INK, width=8)
    x0, y0, x1, y1 = box
    if "\n" in text:                                   # 明示した改行を優先
        ls = text.split("\n")
        while max(d.textlength(l, font=font(size, "Black")) for l in ls) > x1 - x0 - 80 and size > 20:
            size -= 2
        f = font(size, "Black")
    else:
        f, ls = fit(d, text, size, "Black", x1 - x0 - 80, lines)
    lh = int(f.size * 1.2)
    y = (y0 + y1) // 2 - lh * len(ls) // 2
    for l in ls:
        d.text(((x0 + x1) // 2, y + lh // 2), l, font=f, fill=INK, anchor="mm")
        y += lh


def pill(d, cx, y, text, size, fill, color):
    f = font(size, "Black")
    w = d.textlength(text, font=f)
    h = int(size * 2.1)
    d.rounded_rectangle((cx - w / 2 - 44, y, cx + w / 2 + 44, y + h), h // 2, fill=fill)
    d.text((cx, y + h / 2), text, font=f, fill=color, anchor="mm")


def big_cat(img, d, t, emo, prop, x, y, h, ring=True):
    ch = cat(t, h, emo, prop)
    if ring:
        d.ellipse((x - 20, y + 20, x + int(h * 1.0), y + h + 20), fill=tint(COLOR[t], 0.45))
    img.paste(ch, (x, y), ch)


# ---------- H1: 1投稿1ネタ。4枚で終わる3コマ劇場 ----------
def h1():
    T = 4
    lab = "# 本音、誤爆。"
    p = []
    img, d = base("#ff5a4d", lab, 1, T)
    d.text((60, 136), "会議で10秒、誰も喋らない。", font=font(62, "Black"), fill="white")
    bubble(d, (44, 240, W - 44, 560), "意見が出そろいましたね", "white", 124, 2, [(240, 556), (200, 640), (340, 556)])
    big_cat(img, d, "ESTJ", "smug", "stopwatch", 60, 600, 640)
    pill(d, 800, 1140, "本音は →", 56, INK, YELLOW)
    p.append(img)
    img, d = base("#ff5a4d", lab, 2, T)
    pill(d, W // 2, 136, "全員宛てに誤爆しました", 40, INK, YELLOW)
    bubble(d, (44, 250, W - 44, 570), "沈黙は同意とみなす", YELLOW, 130, 2, [(240, 566), (200, 650), (340, 566)])
    big_cat(img, d, "ESTJ", "flat", "stopwatch", 60, 610, 640)
    d.text((W - 60, 1180), "締めたがる人", font=font(54, "Black"), fill="white", anchor="ra")
    p.append(img)
    img, d = base(BG, lab, 3, T)
    bubble(d, (44, 150, W - 44, 470), "まだ誰も同意してないよ", "white", 124, 2, [(760, 466), (800, 550), (880, 466)])
    big_cat(img, d, "ENTP", "smug", "bulb", 420, 520, 640)
    a = avatar("ESTJ", "shock", 260)
    img.paste(a, (70, 860), a)
    d.text((200, 1150), "締めたがる人", font=font(34, "Black"), fill=MUTED, anchor="ma")
    d.text((W - 60, 1220), "逆張りする人", font=font(54, "Black"), fill=INK, anchor="ra")
    p.append(img)
    img, d = base(DARK, lab, 4, T)
    d.text((W // 2, 130), "部長 が入力中…", font=font(48, "Black"), fill="#c3c9d9", anchor="ma")
    d.ellipse((240, 230, 840, 830), fill="#565d70")
    hd = draw_head("BOSS", "flat", 600)
    img.paste(hd, (240, 224), hd)
    bubble(d, (44, 850, W - 44, 1050), "私も何の会議か分かってません。", YELLOW, 70, 1)
    d.rounded_rectangle((44, 1080, W - 44, 1300), 40, fill="white")
    d.text((W // 2, 1136), "あなたの職場の「締めたがる人」、", font=font(40, "Black"), fill=INK, anchor="mm")
    d.text((W // 2, 1216), "誰か分かったら → その人に送る", font=font(52, "Black"), fill=RED, anchor="mm")
    p.append(img)
    return p


# ---------- H2: 2人の関係。送る相手が最初から決まっている ----------
def h2():
    T = 4
    lab = "# この2人、同じ会議にいます"
    p = []
    img, d = base("#7c5cff", lab, 1, T)
    d.text((W // 2, 150), "締めたがる上司", font=font(84, "Black"), fill="white", anchor="ma")
    d.text((W // 2, 262), "×", font=font(80, "Black"), fill=YELLOW, anchor="ma")
    d.text((W // 2, 356), "言えずに飲み込む部下", font=font(84, "Black"), fill="white", anchor="ma")
    big_cat(img, d, "ESTJ", "smug", "stopwatch", 10, 520, 520)
    big_cat(img, d, "INFP", "dead", "mug", 520, 520, 520)
    bubble(d, (44, 1060, W - 44, 1200), "会議で10秒黙ると、こうなる。", "white", 62, 1)
    pill(d, W // 2, 1226, "あなたはどっち？　相方に送って →", 40, INK, YELLOW)
    p.append(img)
    img, d = base(BG, lab, 2, T)
    d.text((60, 136), "表向き", font=font(60, "Black"), fill=INK)
    a = avatar("ESTJ", "smug", 230)
    img.paste(a, (44, 250), a)
    bubble(d, (300, 250, W - 44, 480), "意見が出そろいましたね", "white", 76, 2, [(304, 330), (262, 366), (304, 400)])
    d.text((300, 496), "締めたがる上司", font=font(34, "Black"), fill=COLOR["ESTJ"])
    a = avatar("INFP", "smug", 230)
    img.paste(a, (W - 274, 640), a)
    bubble(d, (44, 640, W - 300, 870), "（口を開きかけて、お茶を飲む）", "white", 60, 2, [(W - 304, 720), (W - 262, 756), (W - 304, 790)])
    d.text((W - 300, 886), "言えずに飲み込む部下", font=font(34, "Black"), fill=COLOR["INFP"], anchor="ra")
    pill(d, W // 2, 1100, "2人の本音は →", 60, INK, YELLOW)
    p.append(img)
    img, d = base("#ff5a4d", lab, 3, T)
    d.text((60, 136), "本音（全員宛てに誤爆）", font=font(56, "Black"), fill="white")
    big_cat(img, d, "ESTJ", "flat", "stopwatch", 20, 250, 400)
    bubble(d, (430, 280, W - 44, 560), "沈黙は同意とみなす", YELLOW, 84, 2, [(434, 380), (390, 420), (434, 450)])
    big_cat(img, d, "INFP", "blank", "mug", 580, 700, 400)
    bubble(d, (44, 740, 600, 1020), "脳内では熱弁をふるった", YELLOW, 76, 2, [(596, 840), (640, 880), (596, 910)])
    pill(d, W // 2, 1180, "部長 がスクショを撮りました", 42, DARK, "white")
    p.append(img)
    img, d = base("#fff7cc", lab, 4, T)
    d.text((60, 136), "この2人の取扱説明書", font=font(64, "Black"), fill=INK)
    for k, (t, who, tip) in enumerate((("ESTJ", "締めたがる上司へ", "「あとでチャットでもいいよ」と一言足す"),
                                       ("INFP", "飲み込む部下へ", "「3秒ください」は言っていい"))):
        y = 260 + k * 400
        d.rounded_rectangle((44, y, W - 44, y + 360), 40, fill="white", outline=INK, width=6)
        a = avatar(t, "normal", 200)
        img.paste(a, (70, y + 80), a)
        d.text((300, y + 40), who, font=font(46, "Black"), fill=COLOR[t])
        f, ls = fit(d, tip, 58, "Black", W - 400, 3)
        yy = y + 120
        for l in ls:
            d.text((300, yy), l, font=f, fill=INK)
            yy += int(f.size * 1.3)
    d.rounded_rectangle((44, 1090, W - 44, 1300), 40, fill=INK)
    d.text((W // 2, 1150), "「これ、私たちだ」と思ったら", font=font(40, "Black"), fill="white", anchor="mm")
    d.text((W // 2, 1232), "相方に送る →", font=font(72, "Black"), fill=YELLOW, anchor="mm")
    p.append(img)
    return p


# ---------- H3: 4択診断。タイプを知らなくても参加できる ----------
def h3():
    T = 5
    lab = "# 10秒でわかる職場タイプ"
    picks = [("A", "ESTJ", "「では決定で」と締める", "stopwatch"), ("B", "ENFJ", "誰かに話を振る", "megaphone"),
             ("C", "ISFJ", "議事録を取り始める", "checklist"), ("D", "ESTP", "とりあえず立ち上がる", "gantt")]
    warn = {"ESTJ": "「逆張りする人」にツッコまれます", "ENFJ": "振った相手は、だいたい田中さん",
            "ISFJ": "その議事録、誰も読んでません", "ESTP": "資料は先週、届いています"}
    p = []
    img, d = base("#12b3a6", lab, 1, T)
    d.text((60, 130), "会議で10秒、誰も喋らない。", font=font(60, "Black"), fill="white")
    d.text((56, 214), "あなたは、どうする？", font=font(104, "Black"), fill=YELLOW, stroke_width=8, stroke_fill=INK)
    for k, (key, t, act, _) in enumerate(picks):
        y = 380 + k * 196
        d.rounded_rectangle((44, y, W - 44, y + 176), 44, fill="white", outline=INK, width=7)
        d.ellipse((70, y + 28, 190, y + 148), fill=INK)
        d.text((130, y + 88), key, font=font(72, "Black"), fill=YELLOW, anchor="mm")
        f, ls = fit(d, act, 64, "Black", W - 300, 1)
        d.text((224, y + 88), ls[0], font=f, fill=INK, anchor="lm")
    pill(d, W // 2, 1190, "選んでからスワイプ →　本音がバレます", 40, INK, "white")
    p.append(img)
    for n, (key, t, act, prop) in enumerate(picks, start=2):
        it = IT[t]
        img, d = base(BG, lab, n, T)
        d.ellipse((50, 130, 190, 270), fill=INK)
        d.text((120, 200), key, font=font(84, "Black"), fill=YELLOW, anchor="mm")
        d.text((214, 136), "を選んだあなたは", font=font(44, "Black"), fill=MUTED)
        f, ls = fit(d, it["role"], 92, "Black", W - 270, 1)
        d.text((212, 190), ls[0], font=f, fill=INK)
        d.rounded_rectangle((44, 310, W - 44, 800), 40, fill=tint(COLOR[t], 0.6))
        emo = it["emotion"] if it["emotion"] != "smug" else "flat"
        ch = cat(t, 470, emo, prop)
        img.paste(ch, ((W - ch.width) // 2 + 30, 320), ch)
        d.text((80, 330), "本音", font=font(40, "Black"), fill=RED)
        bubble(d, (44, 824, W - 44, 1010), it["voice"], YELLOW, 96, 1)
        d.rounded_rectangle((44, 1034, W - 44, 1150), 30, fill="white")
        d.text((80, 1052), "注意", font=font(30, "Black"), fill=RED)
        f, ls = fit(d, warn[t], 44, "Black", W - 280, 1)
        d.text((190, 1066), ls[0], font=f, fill=INK)
        if n < T:
            pill(d, W // 2, 1190, f"16タイプでいうと {t} っぽい　→", 38, INK, "white")
        else:
            d.rounded_rectangle((44, 1176, W - 44, 1310), 40, fill=INK)
            d.text((W // 2, 1216), "結果（A〜D）をコメント。", font=font(38, "Black"), fill="white", anchor="mm")
            d.text((W // 2, 1270), "同僚にもやらせて、答え合わせ →", font=font(44, "Black"), fill=YELLOW, anchor="mm")
        p.append(img)
    return p


if __name__ == "__main__":
    out = ROOT / "samples" / "hypo"
    out.mkdir(parents=True, exist_ok=True)
    allp = []
    for name, fn in (("H1", h1), ("H2", h2), ("H3", h3)):
        for n, im in enumerate(fn(), start=1):
            im = handify(im, n * 31 + ord(name[1]))
            im.save(out / f"{name}_{n:02d}.jpg", quality=92)
            allp.append(im)
    cols = 5
    sheet = Image.new("RGB", (cols * 560, 3 * 720), "#888")
    i = 0
    for r, cnt in enumerate((4, 4, 5)):
        for c in range(cnt):
            sheet.paste(allp[i].resize((540, 675)), (c * 560 + 10, r * 720 + 22))
            i += 1
    sheet.save(out / "sheet.jpg", quality=88)

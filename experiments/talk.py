"""1投稿=1〜2タイプ。「いるいる」と「議論」を狙う形式の試作。 usage: python -m experiments.talk [出力名] [案...]"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from bot.characters import COLOR, NICK, draw as cat
from bot.render import BG, H, INK, MUTED, W, YELLOW, avatar, fit, font, handify, tint
from experiments.hypo import base, bubble, pill

ROOT = Path(__file__).resolve().parent.parent
DARK, RED, BLUE = "#22283a", "#ff5a4d", "#2f7bff"


def lines(d, text, size, weight, box_w, x, y, fill, max_lines=3, gap=1.25, anchor="la"):
    if "\n" in text:                                   # 明示した改行はそのまま使い、全行が収まる大きさにする
        ls = text.split("\n")
        while max(d.textlength(l, font=font(size, weight)) for l in ls) > box_w and size > 20:
            size -= 2
        f = font(size, weight)
    else:
        f, ls = fit(d, text, size, weight, box_w, max_lines)
    for l in ls:
        d.text((x, y), l, font=f, fill=fill, anchor=anchor)
        y += int(f.size * gap)
    return y


def cover(lab, bg, pre, big, t, emo, prop, tagtxt, chips, total, t2=None, emo2="flat", prop2=""):
    img, d = base(bg, lab, 1, total)
    d.text((60, 128), pre, font=font(50, "Black"), fill="white")
    if "\n" in big:                                    # 表紙は意味の切れ目で改行する
        ls, size_ = big.split("\n"), 118
        while max(d.textlength(l, font=font(size_, "Black")) for l in ls) > W - 170:
            size_ -= 2
        f = font(size_, "Black")
    else:
        f, ls = fit(d, big, 112, "Black", W - 170, 4)
    lh = int(f.size * 1.2)
    bh = lh * len(ls) + 60
    d.rounded_rectangle((44, 206, W - 44, 206 + bh), 52, fill="white", outline=INK, width=8)
    y = 206 + 28
    for l in ls:
        d.text((84, y), l, font=f, fill=INK)
        y += lh
    top = 206 + bh + 20
    size = min(540, H - top - 30)
    d.ellipse((10, H - size - 10, size + 10, H - 10), fill=tint(COLOR[t], 0.45))
    ch = cat(t, size, emo, prop)
    img.paste(ch, (0, H - size - 24), ch)
    if t2:
        d.ellipse((W - size + 60, H - size - 10, W + 60, H - 10), fill=tint(COLOR[t2], 0.45))
        ch2 = cat(t2, size - 60, emo2, prop2)
        img.paste(ch2, (W - ch2.width + 40, H - size + 30), ch2)
        pill(d, W // 2, top + 6, tagtxt, 34, INK, "white")
        for k, (txt, col) in enumerate(chips):
            pill(d, W // 2, H - 250 + k * 110, txt, 50, col, "white")
    else:
        cx = (size + 40 + W) // 2
        ts = 36
        while d.textlength(tagtxt, font=font(ts, "Black")) + 88 > W - size - 60:
            ts -= 2
        pill(d, cx, top + 30, tagtxt, ts, INK, "white")
        for k, (txt, col) in enumerate(chips):
            pill(d, cx, top + 150 + k * 130, txt, 64, col, "white")
        d.text((cx, H - 120), "あなたはどっち？ →", font=font(40, "Black"), fill="white", anchor="mm")
    return img


def obs(lab, title, rows, t, emo, page, total, foot, bg=BG, phone=False):
    img, d = base(bg, lab, page, total)
    lines(d, title, 62, "Black", W - 320, 60, 128, INK, 2)
    a = avatar(t, emo, 190)
    img.paste(a, (W - 240, 116), a)
    n = len(rows)
    ph = (1160 - 320) // n
    for k, (when, text) in enumerate(rows):
        y = 320 + k * ph
        d.rounded_rectangle((44, y, (W - 330) if phone else (W - 44), y + ph - 22), 36, fill="white", outline=INK, width=5)
        f = font(34, "Black")
        w = d.textlength(when, font=f) + 44
        d.rounded_rectangle((70, y + 22, 70 + w, y + 82), 30, fill=INK)
        d.text((92, y + 52), when, font=f, fill=YELLOW, anchor="lm")
        lines(d, text, 54 if not phone else 40, "Black", (W - 160) if not phone else (W - 440), 78, y + (100 if not phone else 92), INK, 2, 1.2)
    if phone:                                           # 600字の長文が届いた画面
        d.rounded_rectangle((W - 306, 330, W - 44, 1140), 44, fill=INK)
        d.rounded_rectangle((W - 290, 372, W - 60, 1098), 20, fill="white")
        d.text((W - 175, 400), "15:07", font=font(34, "Black"), fill=MUTED, anchor="mm")
        d.rounded_rectangle((W - 278, 432, W - 72, 1030), 22, fill="#dfe9ff")
        import random
        r = random.Random(7)
        for i in range(26):
            wln = 182 if i % 6 else 90
            wln = int(wln * r.uniform(0.82, 1.0))
            d.line([(W - 266, 452 + i * 22), (W - 266 + wln, 452 + i * 22)], fill="#5b6475", width=7)
        d.text((W - 175, 1064), "600字", font=font(40, "Black"), fill="#d1495b", anchor="mm")
    pill(d, W // 2, 1200, foot, 44, INK, YELLOW)
    return img


def voices(lab, title, items, page, total, foot, bg=BG, title_fill=INK):
    img, d = base(bg, lab, page, total)
    lines(d, title, 62, "Black", W - 120, 60, 128, title_fill, 1)
    n = len(items)
    ph = (1170 - 240) // n
    for k, (t, emo, role, text, fill) in enumerate(items):
        y = 240 + k * ph
        left = k % 2 == 0
        size = min(210, ph - 60)
        a = avatar(t, emo, size)
        ax = 44 if left else W - 44 - size
        img.paste(a, (ax, y + 10), a)
        d.text((ax + size // 2, y + size + 18), role, font=font(28, "Black"), fill=COLOR[t], anchor="ma")
        bx0, bx1 = (44 + size + 40, W - 44) if left else (44, W - 44 - size - 40)
        tail = [(bx0 + 4, y + 70), (bx0 - 34, y + 100), (bx0 + 4, y + 130)] if left else [(bx1 - 4, y + 70), (bx1 + 34, y + 100), (bx1 - 4, y + 130)]
        bubble(d, (bx0, y + 6, bx1, y + ph - 40), text, fill, 62, 3, tail)
    pill(d, W // 2, 1200, foot, 44, INK, YELLOW)
    return img


def vote(lab, q, a, b, ta, tb, ea, eb, arg_a, arg_b, cta, page, total, c=None):
    img, d = base(BG, lab, page, total)
    y0 = lines(d, q, 78, "Black", W - 120, 60, 126, INK, 2)
    hh = 300 if c else 350
    top = max(y0 + 16, 330)
    for k, (key, colr, t, emo, lbl, arg) in enumerate((("A", RED, ta, ea, a, arg_a), ("B", BLUE, tb, eb, b, arg_b))):
        y = top + k * (hh + 22)
        d.rounded_rectangle((44, y, W - 44, y + hh), 44, fill=colr, outline=INK, width=7)
        av = avatar(t, emo, 210)
        img.paste(av, (70, y + (hh - 210) // 2), av)
        d.text((320, y + 22), key, font=font(90, "Black"), fill="white")
        f, ls = fit(d, lbl, 84, "Black", W - 480, 1)
        d.text((420, y + 32), ls[0], font=f, fill="white")
        lines(d, arg, 46, "Black", W - 400, 320, y + 150, "white", 2, 1.3)
    y = top + 2 * (hh + 22)
    if c:
        d.rounded_rectangle((44, y, W - 44, y + 96), 40, fill="white", outline=INK, width=6)
        d.text((80, y + 48), "C", font=font(60, "Black"), fill=INK, anchor="lm")
        f, ls = fit(d, c, 46, "Black", W - 260, 1)
        d.text((150, y + 48), ls[0], font=f, fill=INK, anchor="lm")
        y += 116
    d.rounded_rectangle((44, y, W - 44, 1320), 40, fill=INK)
    mid = (y + 1320) // 2
    d.text((W // 2, mid - 34), "A か B、理由を一言でコメント", font=font(46, "Black"), fill=YELLOW, anchor="mm")
    d.text((W // 2, mid + 34), cta, font=font(34, "Black"), fill="white", anchor="mm")
    return img


def scene_cover(lab, bg, pre, big, tagtxt, chips, total, hero, others, ask, clock=None):
    """表紙を場面の絵にする: 発言が飛び交う会議卓で、主役だけ黙っている。"""
    img, d = base(bg, lab, 1, total)
    d.text((60, 128), pre, font=font(50, "Black"), fill="white")
    ls, size_ = big.split("\n"), 150
    while max(d.textlength(l, font=font(size_, "Black")) for l in ls) > W - 170:
        size_ -= 2
    f = font(size_, "Black")
    lh = int(f.size * 1.2)
    bh = lh * len(ls) + 56
    d.rounded_rectangle((44, 206, W - 44, 206 + bh), 52, fill="white", outline=INK, width=8)
    y = 206 + 26
    for l in ls:
        d.text((84, y), l, font=f, fill=INK)
        y += lh
    top = 206 + bh + 16
    pill(d, W // 2, top, tagtxt, 32, INK, "white")
    by = top + 96
    avail = H - 170 - by                                  # 場面は空いた高さいっぱいに描く
    hs, os_ = min(avail - 10, 520), int(min(avail - 10, 520) * 0.74)
    for k, (t, emo, prop) in enumerate(others):          # 奥で喋っている2人
        ch = cat(t, os_, emo, prop)
        x = -10 if k == 0 else W - ch.width + 40
        img.paste(ch, (x, H - 170 - os_ - 70), ch)
        if clock:
            continue
        bx = 230 if k == 0 else W - 450
        d.rounded_rectangle((bx, by - 10, bx + 220, by + 90), 30, fill="white", outline=INK, width=5)
        for i, wl in enumerate((160, 120)):
            d.line([(bx + 28, by + 24 + i * 30), (bx + 28 + wl, by + 24 + i * 30)], fill=INK, width=8)
    d.rounded_rectangle((20, H - 280, W - 20, H - 180), 40, fill="#b98b5e", outline=INK, width=7)   # 会議卓
    t, emo, prop = hero
    ch = cat(t, hs, emo, prop)
    img.paste(ch, ((W - ch.width) // 2 + 40, H - 176 - hs), ch)
    if clock:                                           # 壁のデジタル時計
        fc = font(84, "Black")
        cw = d.textlength(clock, font=fc) + 90
        d.rounded_rectangle((W // 2 - cw / 2, by - 14, W // 2 + cw / 2, by + 112), 26, fill=INK, outline="white", width=6)
        d.text((W // 2, by + 46), clock, font=fc, fill="#ff5a4d", anchor="mm")
    else:
        d.rounded_rectangle((W // 2 - 84, by - 6, W // 2 + 84, by + 74), 30, fill=YELLOW, outline=INK, width=5)
        d.text((W // 2, by + 28), "……", font=font(44, "Black"), fill=INK, anchor="mm")
    d.rectangle((0, H - 170, W, H), fill=INK)
    d.text((40, H - 150), ask, font=font(36, "Black"), fill="white")
    x = 40
    for txt, col in chips:
        fch = font(50, "Black")
        w = d.textlength(txt, font=fch) + 70
        d.rounded_rectangle((x, H - 100, x + w, H - 18), 41, fill=col)
        d.text((x + w / 2, H - 59), txt, font=fch, fill="white", anchor="mm")
        x += w + 24
    d.text((W - 40, H - 59), "→", font=font(60, "Black"), fill=YELLOW, anchor="rm")
    return img


# ===== 題材: 会議では黙って、終わった後に長文チャットを送る人 =====
T, O = "INFP", "ESTJ"


def v1():
    """本人の言い分 vs 周りの本音(1タイプ)"""
    lab, n = "# いる、こういう人。", 5
    return [
        cover(lab, "#7c5cff", "いる、こういう人。", "会議では黙って、\n終わった後に\n長文を送ってくる人", T, "blank", "mug",
              "INFPに多い", [("アリ？", RED), ("ナシ？", BLUE)], n),
        obs(lab, "観察記録", [("14:00 会議中", "うなずくだけ。発言ゼロ"), ("15:07 終了7分後", "チャットに600字が届く"),
                          ("書き出し", "「先ほどの件ですが…」"), ("締め", "「的外れでしたらすみません」")], T, "blank", 2, n, "しかも、内容は一番まとも →"),
        voices(lab, "周りの本音", [(O, "angry", "隣の席の人", "それ、さっき言ってくれたら10分で終わった", "white"),
                               ("ENTJ", "flat", "上司", "読むのに5分、返信に15分", "white"),
                               ("ENFP", "sparkle", "後輩", "でも一番まともな意見、いつもこの人", YELLOW)], 3, n, "本人の言い分は →"),
        voices(lab, "本人の言い分", [(T, "sweat", "本人", "話しながら考えるのが、無理なんです", YELLOW),
                                (T, "dead", "本人", "言おうとした時には、話題が3つ先", YELLOW),
                                (T, "cry", "本人", "口だと3割。文字なら全部出せる", YELLOW)], 4, n, "さて、どっち？ →", "#ffe9e6"),
        vote(lab, "会議の後に長文、アリ？ナシ？", "アリ", "ナシ", T, O, "sweat", "angry",
             "中身が良ければ、いつ言ってもいい", "その場で言わないなら、会議の意味がない", "理由を書くと、反対派から返信が来ます", 5, n),
    ]


def v2():
    """職場裁判(検察 vs 弁護、判決はコメント欄)"""
    lab, n = "# 職場裁判", 5
    return [
        cover(lab, DARK, "職場裁判・本日の被告", "会議では黙って、\n終わった後に\n長文を送ってくる人", T, "sweat", "mug",
              "被告：INFPに多い", [("有罪？", RED), ("無罪？", BLUE)], n),
        obs(lab, "証拠品", [("14:00〜15:00", "会議中の発言回数：0回"), ("15:07", "チャット送信：600字"),
                         ("本文の冒頭", "「先ほどの件ですが…」"), ("本文の末尾", "「的外れでしたらすみません」")], T, "sweat", 2, n, "検察の主張 →"),
        voices(lab, "検察側の主張", [(O, "angry", "検察：隣の席の人", "その場で言えば10分で終わった話です", "white"),
                               (O, "flat", "検察", "決まった後にひっくり返すのは、全員の時間泥棒", "white"),
                               ("ENTJ", "angry", "証人：上司", "返信に15分。私の残業の原因です", "white")], 3, n, "弁護側の主張 →", "#ffe9e6"),
        voices(lab, "弁護側の主張", [(T, "sweat", "被告本人", "話しながら考えるのが、無理なんです", YELLOW),
                               ("ENFP", "sparkle", "弁護人：後輩", "その長文、いつも一番まともです", YELLOW),
                               ("ENFP", "normal", "弁護人", "声の大きい人だけで決めていいんですか", YELLOW)], 4, n, "判決は、あなたが →", "#e6f0ff"),
        vote(lab, "判決を、コメント欄で。", "有罪", "無罪", O, T, "angry", "sweat",
             "その場で言わないのは、会議のルール違反", "良い意見に、提出期限はない", "量刑(罰ゲーム)も募集しています", 5, n),
    ]


def v3():
    """2タイプのすれ違い(同じ1時間を、2人の心の声で)"""
    lab, n = "# 同じ会議、ちがう世界", 5
    return [
        cover(lab, "#12b3a6", "同じ会議に出ていた2人", "その場で決めたい人\n×\n後から長文の人", O, "flat", "stopwatch",
              "ESTJに多い × INFPに多い", [("どっちの気持ちが分かる？", INK)], n, T, "blank", "mug"),
        voices(lab, "14:00 会議中", [(O, "smug", "その場で決めたい人", "反対意見なし。よし、決定", "white"),
                                 (T, "blank", "後から長文の人", "（反対だけど、言葉がまとまらない）", YELLOW),
                                 (O, "flat", "その場で決めたい人", "沈黙は同意とみなします", "white")], 2, n, "そして会議のあと →"),
        voices(lab, "15:07 会議のあと", [(T, "sweat", "後から長文の人", "600字、送信。「先ほどの件ですが」", YELLOW),
                                   (O, "shock", "その場で決めたい人", "今？　もう議事録を送ったんだけど", "white"),
                                   (T, "dead", "後から長文の人", "送ってから30分、返信が怖くて動けない", YELLOW)], 3, n, "2人の言い分 →"),
        voices(lab, "それぞれの言い分", [(O, "angry", "その場で決めたい人", "その場で言えば、10分で終わった", "white"),
                                 (T, "cry", "後から長文の人", "話しながら考えるのが、無理なんです", YELLOW)], 4, n, "さて、どっち？ →", "#fff7cc"),
        vote(lab, "どっちの気持ちが分かる？", "その場派", "長文派", O, T, "angry", "sweat",
             "言いたいことは、会議の中で言ってほしい", "考えてから言わせてほしい", "「うちの職場はこう」も教えてください", 5, n),
    ]


def v4():
    """V1の改良: 両側の言い分を対等にし、問いを「決定をやり直すか」にする"""
    lab, n = "# いる、こういう人。", 5
    return [
        cover(lab, "#7c5cff", "いる、こういう人。", "会議では一言も喋らず、\n7分後に600字\n送ってくる人", T, "blank", "phone",
              "職場に1人はいる（INFPに多い）", [("アリ？", RED), ("ナシ？", BLUE)], n),
        obs(lab, "観察記録", [("14:00 会議中", "発言ゼロ。メモは誰よりも取っている"), ("15:07 終了7分後", "「先ほどの件ですが」で始まる600字"),
                          ("送信前", "3回読み返し、絵文字を足して、消す"), ("締めの一文", "「的外れでしたらすみません」")],
            T, "blank", 2, n, "で、周りの本音は →", phone=True),
        voices(lab, "周りの本音", [(O, "angry", "隣の席の人", "その600字、会議なら30秒で言えた", "white"),
                               ("ENTJ", "shock", "上司", "決定は15:00に、もう客先へ送った後でした", "white"),
                               ("ENFP", "sweat", "後輩", "先月のミス、気づいてたのはこの長文だけ", "white")], 3, n, "本人の言い分は →"),
        voices(lab, "本人の言い分", [(T, "sweat", "本人", "頭の中で清書しないと、口から出せない", YELLOW),
                                (T, "dead", "本人", "下書きを直していたら、14:40でした", YELLOW),
                                (T, "cry", "本人", "送る前に3回読んで、送った後30分固まる", YELLOW)], 4, n,
               "INFP＝考えを内側で仕上げてから出す人 →", "#ffe9e6"),
        vote(lab, "あなたが上司なら、\nこの600字で決定をやり直す？", "やり直す", "変えない", "ENFP", O, "sweat", "angry",
             "良い意見に、提出期限はない", "決まった後の意見は、次回に回す", "理由を書くと、反対派から返信が来ます", 5, n,
             c="そもそも、会議の進め方が悪い"),
    ]


def v5():
    """V4の改良: 600字の中身を明示、逃げ道のCを削除、表紙を会議の場面に"""
    lab, n = "# いる、こういう人。", 5
    return [
        scene_cover(lab, "#7c5cff", "いる、こういう人。", "会議では一言も喋らず、\n7分後に600字\n送ってくる人",
                    "考えてから話すINFPに多い", [("やり直す？", RED), ("変えない？", BLUE)], n,
                    (T, "blank", "checklist"), [(O, "angry", "stopwatch"), ("ENTJ", "flat", "megaphone")],
                    "その600字で、もう決まったことを"),
        obs(lab, "観察記録", [("14:00 会議中", "発言ゼロ。メモは誰よりも取っている"), ("15:07 終了7分後", "「先ほどの件ですが」で始まる600字"),
                          ("送信前", "3回読み返し、絵文字を足して、消す"), ("600字の中身", "「B案なら、納期が3日早くなります」")],
            T, "blank", 2, n, "で、周りの本音は →", phone=True),
        voices(lab, "周りの本音", [(O, "angry", "隣の席の人", "その600字、会議なら30秒で言えた", "white"),
                               ("ENTJ", "shock", "上司", "A案で決定、と15:00に全員へ送った後でした", "white"),
                               ("ENFP", "sweat", "後輩", "先月のミス、気づいてたのはこの長文だけ", "white")], 3, n, "本人の言い分は →"),
        voices(lab, "本人の言い分", [(T, "sweat", "本人", "14:10に言いかけて、話題が次へ移った", YELLOW),
                                (T, "dead", "本人", "下書きを直していたら、14:40でした", YELLOW),
                                (T, "cry", "本人", "送る前に3回読んで、送った後30分固まる", YELLOW)], 4, n,
               "INFP＝口より先に、頭の中で下書きを書く人 →", "#ffe9e6"),
        vote(lab, "あなたが上司なら、\nこの600字で決定をやり直す？", "やり直す", "変えない", "ENFP", O, "sweat", "angry",
             "良い意見に、提出期限はない", "決まった後の意見は、次回に回す", "長文を送る側の人、言い分をどうぞ", 5, n),
    ]


def v6():
    """V5の改良: 両側の損得を釣り合わせ、問いを「職場のルールにするなら」に"""
    lab, n = "# いる、こういう人。", 5
    return [
        scene_cover(lab, "#7c5cff", "考えてから話すINFPに多い", "会議は無言。\n7分後に600字。",
                    "職場に1人はいる", [("受け付ける？", RED), ("次回に回す？", BLUE)], n,
                    (T, "blank", "phone"), [(O, "angry", "stopwatch"), ("ENTJ", "flat", "megaphone")],
                    "会議が終わった後の意見、"),
        obs(lab, "観察記録", [("14:00 会議中", "発言ゼロ。メモは誰よりも取っている"), ("15:07 終了7分後", "「否定したい訳ではないのですが」"),
                          ("送信前", "3回読み返し、絵文字を足して、消す"), ("600字の中身", "「A案だと、納期が3日遅れます」")],
            T, "blank", 2, n, "で、周りの本音は →", phone=True),
        voices(lab, "周りの本音", [(O, "angry", "隣の席の人", "会議後の長文、\n今月これで3回目です", "white"),
                               ("ENTJ", "shock", "上司", "15:02に発注済み。\n取り消すと全員2時間残業", "white"),
                               ("ENFP", "sweat", "後輩", "でも先月のミス、\n気づいたのはこの長文だけ", "white")], 3, n, "本人の言い分は →"),
        voices(lab, "本人の言い分", [(T, "sweat", "本人", "14:10に言いかけて、\n話題が次へ移った", YELLOW),
                                (T, "dead", "本人", "下書きの完成は14:58。\nもう締めの挨拶でした", YELLOW),
                                (T, "cry", "本人", "送る前に3回読んで、\n送った後30分固まる", YELLOW)], 4, n,
               "頭の中で下書きを書く人。順番が逆なだけ →", "#ffe9e6"),
        vote(lab, "この一件、\n職場のルールにするなら？", "後からOK", "次回に回す", "ENFP", O, "sweat", "angry",
             "会議後24時間は、意見を受け付ける", "会議で出なかった意見は、次回に回す", "長文を送る側の人、言い分をどうぞ", 5, n),
    ]


def build(sp):
    """題材の定義(dict)から5枚を組み立てる。本番の自動生成もこの形のデータを作ればよい。"""
    lab, n, t = "# いる、こういう人。", 5, sp["type"]
    return [
        scene_cover(lab, sp["color"], "いる、こういう人。", sp["cover"], sp["tag"], [(sp["a"] + "？", RED), (sp["b"] + "？", BLUE)], n,
                    (t, sp["hero"][0], sp["hero"][1]), sp["others"], sp["ask"], sp.get("clock")),
        obs(lab, "観察記録", sp["obs"], t, sp["hero"][0], 2, n, "で、周りの本音は →", phone=sp.get("phone", False)),
        voices(lab, "周りの本音", [(tt, e, r, x, "white") for tt, e, r, x in sp["around"]], 3, n, "本人の言い分は →"),
        voices(lab, "本人の言い分", [(t, e, "本人", x, YELLOW) for e, x in sp["self"]], 4, n, sp["punch"] + " →", "#ffe9e6"),
        vote(lab, sp["question"], sp["a"], sp["b"], sp["cat_a"][0], sp["cat_b"][0], sp["cat_a"][1], sp["cat_b"][1],
             sp["arg_a"], sp["arg_b"], "当事者も、振り回される側も、言い分をどうぞ", 5, n),
    ]


CHAT = dict(type="INFP", color="#7c5cff", tag="考えてから話すINFPに多い", phone=True,
            cover="会議では一言も喋らず、\n7分後にチャットで\n600字送ってくる人", ask="もう発注した後。あなたが上司なら",
            hero=("blank", "phone"), others=[("ESTJ", "angry", "stopwatch"), ("ENTJ", "flat", "megaphone")],
            obs=[("14:00 会議中", "発言ゼロ。メモは誰よりも取っている"), ("15:07 終了7分後", "「否定したい訳ではないのですが」"),
                 ("送信前", "3回読み返し、絵文字を足して、消す"), ("600字の中身", "「A案だと、納期が3日遅れます」")],
            around=[("ESTJ", "angry", "隣の席の人", "会議後の長文、\n今月これで3回目です"),
                    ("ENTJ", "shock", "上司", "15:02に発注済み。\n14:10に一言あれば止められた"),
                    ("ENFP", "sweat", "後輩", "でも先月のミス、\n気づいたのはこの長文だけ")],
            self=[("sweat", "14:10に言いかけて、\n話題が次へ移った"), ("dead", "下書きの完成は14:58。\nもう締めの挨拶でした"),
                  ("cry", "送る前に3回読んで、\n送った後30分固まる")],
            punch="黙ってたんじゃない。まだ書いてた",
            question="発注はもう済んでいる。\nあなたが上司なら？", a="取り消す", b="そのまま",
            arg_a="全員2時間残業してでも、3日の遅れを防ぐ", arg_b="決定は覆さない。3日の遅れは受け入れる",
            cat_a=("ENFP", "sweat"), cat_b=("ESTJ", "angry"))

TEIJI = dict(type="ISTP", color="#12b3a6", tag="自分の時間を守るISTPに多い",
             cover="18:00:00に\n席を立つ人", ask="18:03に客先から急ぎの電話。あなたが上司なら",
             hero=("flat", "wrench"), others=[("ESFJ", "sweat", "donut"), ("ENTJ", "angry", "megaphone")],
             obs=[("17:58", "ブラウザのタブを、端から順に閉じ始める"), ("18:00:00", "「お先です」。椅子はもう机の下"),
                  ("18:01以降", "チャットの返信は、翌朝9:00ちょうど"), ("ただし", "今月の成果は、部内で1位")],
             around=[("ESFJ", "sweat", "隣の席の人", "18:05に相談しようと\n思ってたのに、もういない"),
                     ("ENTJ", "angry", "上司", "成果が1位なので、\n何も言えないのが悔しい"),
                     ("ENFP", "sparkle", "後輩", "先輩が帰るから、\n私も18:10に帰れてます")],
             self=[("flat", "定時は約束。破っているのは\n残業のほうです"), ("sweat", "18時に終わらせるため、\n昼休みは15分で戻ってます"),
                   ("sleepy", "18:01からの自分は、\nもう会社の人じゃない")],
             punch="早く帰ってるんじゃない。時間どおりに帰ってる",
             question="18:03、客先から急ぎの電話。\n担当は、もう帰った本人。", a="呼び戻す", b="朝まで待つ",
             arg_a="客先を待たせない。今すぐ本人に電話する", arg_b="定時後は連絡しない。明日9:00に対応させる",
             cat_a=("ENTJ", "angry"), cat_b=("ENFP", "sparkle"))

TEIJI2 = dict(TEIJI, tag="勤務時間は契約、と割り切るISTPに多い", clock="18:00:00",
              hero=("flat", "bag"), others=[("ESFJ", "sweat", "laptop"), ("ENTJ", "angry", "laptop")],
              obs=[("17:58", "ブラウザのタブを、端から順に閉じ始める"), ("18:00:00", "「お先です」。椅子はもう机の下"),
                   ("18:01以降", "チャットの返信は、翌朝9:00ちょうど"), ("ただし", "自分の仕事は、毎日すべて終えている")],
              around=[("ESFJ", "sweat", "隣の席の人", "18:05に相談しようと\n思ってたのに、もういない"),
                      ("ENTJ", "angry", "上司", "先週の18:03の電話、\n私が40分謝りました"),
                      ("ENFP", "sparkle", "後輩", "先輩が帰るから、\n私も18:10に帰れてます")],
              question="18:03、客先から急ぎの電話。\n担当は帰った。あなたが上司なら？")

NOMIKAI = dict(type="INTJ", color="#ff8a1f", tag="一人の時間で回復するINTJに多い",
               cover="飲み会を、毎回\n「予定があります」\nで断る人", ask="新人の歓迎会も欠席。あなたが幹事なら",
               hero=("flat", "mug"), others=[("ESFJ", "sparkle", "cracker"), ("ENFP", "sparkle", "mic")],
               obs=[("出欠の連絡から30秒", "「欠席でお願いします」と返信が来る"), ("理由", "毎回「予定があります」の一言だけ"),
                    ("その夜21:00", "家で3時間煮込んだカレーの写真を投稿"), ("ただし", "昼のランチには、毎回ちゃんと来る")],
               around=[("ESFJ", "sweat", "幹事", "人数は読みやすい。\nでも毎回ちょっと寂しい"),
                       ("ENTJ", "angry", "上司", "新人が「嫌われてますか」\nと私に聞いてきた"),
                       ("ISFP", "sparkle", "後輩", "先輩が断るから、\n私も断れるようになった")],
               self=[("flat", "予定はあります。\n家で一人で過ごす予定が"), ("dead", "飲み会の2時間は、\n回復に2日かかります"),
                     ("sweat", "嫌いなんじゃない。\n昼なら行きます")],
               punch="断ってるんじゃない。選んでる",
               question="新人の歓迎会も「欠席」。\nあなたが幹事なら？", a="来てと頼む", b="何も言わない",
               arg_a="歓迎会だけは別。1時間でいいから出てと頼む", arg_b="飲み会は仕事じゃない。出欠は本人の自由",
               cat_a=("ESFJ", "sweat"), cat_b=("ISFP", "sparkle"))

TEIJI3 = dict(TEIJI, tag="決めた線は1秒も動かさないISTPに多い", clock="18:00:00",
              hero=("flat", "bag"), others=[("ESFJ", "sweat", "laptop"), ("ENTJ", "angry", "laptop")],
              around=[("ESFJ", "sweat", "隣の席の人", "18:05に相談しようと\n思ってたのに、もういない"),
                      ("ENTJ", "angry", "上司", "先週の18:03の電話、\n私が40分謝りました"),
                      ("ENFP", "sparkle", "後輩", "先輩が帰るから、\n私も18:10に帰れてます")],
              self=[("flat", "定時は約束。破っているのは\n残業のほうです"), ("sweat", "18時に終わらせるため、\n昼休みは15分で戻ってます"),
                    ("sleepy", "18:01、社用スマホは\n引き出しの中です")],
              question="18:03、客先から「今日中に」の電話。\n分かるのは帰った担当だけ。", ask="18:03に客先から急ぎの電話。あなたが上司なら")

VARIANTS = {"V1": v1, "V2": v2, "V3": v3, "V4": v4, "V5": v5, "V6": v6, "T5": lambda: build(TEIJI3),
            "T3": lambda: build(TEIJI2), "T4": lambda: build(NOMIKAI),
            "V7": lambda: build(CHAT), "T2": lambda: build(TEIJI)}

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "talk1"
    keys = sys.argv[2:] or list(VARIANTS)
    out = ROOT / "samples" / name
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for k in keys:
        pages = [handify(im, i * 37 + ord(k[-1])) for i, im in enumerate(VARIANTS[k](), start=1)]
        for i, im in enumerate(pages, start=1):
            im.save(out / f"{k}_{i:02d}.jpg", quality=92)
        rows.append(pages)
    cols = max(len(r) for r in rows)
    sheet = Image.new("RGB", (cols * 560, len(rows) * 720), "#888")
    for r, pages in enumerate(rows):
        for c, im in enumerate(pages):
            sheet.paste(im.resize((540, 675)), (c * 560 + 10, r * 720 + 22))
    sheet.save(out / "sheet.jpg", quality=88)

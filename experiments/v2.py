"""別形式(ランキング、1タイプの非公開メモ)の見本と、本番レンダラーの一覧シートを作る。
usage: python -m experiments.v2 [出力dir名]"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from bot import render as R
from bot.characters import COLOR, NICK, draw_head
from bot.render import BG, H, INK, MUTED, W, YELLOW, avatar, fit, font

ROOT = Path(__file__).resolve().parent.parent


# ---------- 別形式(曜日ローテーション用) ----------
def ranking():
    R = json.loads((ROOT / "samples" / "ranking.json").read_text())
    rows = R["rows"]
    img = Image.new("RGB", (W, H), "#7c5cff")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 104), fill="#2b2350")
    d.text((56, 24), "# 本音ランキング速報", font=font(40, "Black"), fill="white")
    d.text((60, 150), "会議の沈黙を", font=font(92, "Black"), fill="white")
    d.text((60, 268), "破るのが早い順。", font=font(92, "Black"), fill=YELLOW)
    d.text((62, 400), "16タイプ全員、秒数つき", font=font(48, "Black"), fill="white")
    t1 = rows[0][0]
    head = draw_head(t1, "angry", 560)
    img.paste(head, (30, 560), head)
    d.rounded_rectangle((600, 640, 1044, 900), 40, fill=YELLOW, outline=INK, width=6)
    d.text((822, 700), "1位", font=font(60, "Black"), fill=INK, anchor="mm")
    d.text((822, 810), rows[0][1], font=font(120, "Black"), fill="#d1495b", anchor="mm")
    d.rounded_rectangle((600, 930, 1044, 1010), 28, fill="white")
    d.rounded_rectangle((626, 950, 800, 990), 8, fill=INK)
    d.text((812, 948), "が最下位", font=font(34, "Black"), fill=INK)
    d.rectangle((0, 1190, W, H), fill="white")
    d.text((44, 1232), "最下位は「翌朝」です", font=font(44, "Black"), fill=INK)
    d.rounded_rectangle((770, 1222, W - 44, 1318), 48, fill=INK)
    d.text((903, 1270), "スワイプ →", font=font(38, "Black"), fill="white", anchor="mm")
    cover_img = img

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 150), fill="#2b2350")
    d.text((56, 30), "# 本音ランキング速報", font=font(44, "Black"), fill="white")
    d.text((58, 96), f'{R["title"]}　16位→9位', font=font(27, "Regular"), fill="#c3c9d9")
    d.text((W - 56, 98), "2/4", font=font(27, "Regular"), fill="#c3c9d9", anchor="ra")
    for k, (t, sec, note) in enumerate(reversed(rows[8:])):
        y = 176 + k * 144
        rank = 16 - k
        d.rounded_rectangle((36, y, W - 36, y + 130), 28, fill="white")
        d.text((92, y + 65), f"{rank}", font=font(58, "Black"), fill=MUTED, anchor="mm")
        a = avatar(t, "sleepy" if rank > 12 else "flat", 112)
        img.paste(a, (150, y + 9), a)
        d.text((282, y + 14), t, font=font(34, "Black"), fill=COLOR[t])
        d.text((282 + d.textlength(t, font=font(34, "Black")) + 12, y + 20), NICK[t], font=font(26), fill=INK)
        d.text((282, y + 66), note, font=font(34, "Bold"), fill=INK)
        fnt, ls = fit(d, sec, 44, "Black", 330, 1)
        d.text((W - 66, y + 65), ls[0], font=fnt, fill="#d1495b", anchor="rm")
    return cover_img, img


def deepdive():
    T = json.loads((ROOT / "samples" / "timeline.json").read_text())
    t, col = T["type"], COLOR[T["type"]]
    img = Image.new("RGB", (W, H), "#12b3a6")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 104), fill="#103b38")
    d.text((56, 24), f"# {t}の非公開メモ", font=font(40, "Black"), fill="white")
    d.text((60, 150), f"{t}の", font=font(92, "Black"), fill="white")
    d.text((60, 268), "日帰り出張、", font=font(92, "Black"), fill="white")
    d.text((60, 386), "心の実況。", font=font(110, "Black"), fill=YELLOW)
    head = draw_head(t, "flat", 560)
    img.paste(head, (0, 620), head)
    d.rounded_rectangle((560, 700, 1044, 850), 40, fill=YELLOW, outline=INK, width=6)
    d.text((802, 775), T["cover"]["text"], font=font(62, "Black"), fill=INK, anchor="mm")
    d.text((1040, 866), "17:30 駅の売店にて", font=font(30), fill="white", anchor="ra")
    d.rectangle((0, 1190, W, H), fill="white")
    d.text((44, 1232), "06:50から20:45まで全5件", font=font(42, "Black"), fill=INK)
    d.rounded_rectangle((770, 1222, W - 44, 1318), 48, fill=INK)
    d.text((903, 1270), "スワイプ →", font=font(38, "Black"), fill="white", anchor="mm")
    cover_img = img

    img = Image.new("RGB", (W, H), "#fffbea")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 150), fill="#103b38")
    d.text((56, 30), f"# {t}の非公開メモ", font=font(44, "Black"), fill="white")
    d.text((58, 96), "日帰り出張の日　※本人以外は閲覧できません", font=font(27, "Regular"), fill="#c3d9d6")
    for k, it in enumerate(T["items"][:4]):
        y = 180 + k * 286
        a = avatar(t, it["emotion"], 170)
        img.paste(a, (36, y + 10), a)
        d.text((240, y), it["time"], font=font(60, "Black"), fill=col)
        d.text((430, y + 22), it["place"], font=font(32), fill=MUTED)
        d.text((240, y + 80), "▷ " + it["action"], font=font(33, "Bold"), fill="#1f2937")
        fnt, ls = fit(d, it["voice"], 54, "Black", 700, 1)
        bw = d.textlength(ls[0], font=fnt) + 68
        d.rounded_rectangle((236, y + 136, 236 + bw, y + 246), 30, fill=YELLOW if k == 3 else "white", outline=INK, width=4)
        d.text((270, y + 156), ls[0], font=fnt, fill=INK)
    return cover_img, img


def main(name="final"):
    out = ROOT / "samples" / name
    post = json.loads((ROOT / "samples" / "all16.json").read_text())
    pages = [Image.open(p) for p in R.render(post, out)]
    cols = 4
    rows = -(-len(pages) // cols)
    sheet = Image.new("RGB", (cols * 560, rows * 720), "#888")
    for i, im in enumerate(pages):
        sheet.paste(im.resize((540, 675)), ((i % cols) * 560 + 10, (i // cols) * 720 + 22))
    sheet.save(out / "sheet.jpg", quality=88)


if __name__ == "__main__":
    main(*sys.argv[1:])

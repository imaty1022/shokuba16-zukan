"""今日のネタを選び、Claude APIで「本音チャット誤爆」形式の投稿内容(JSON)を作る。

usage: python -m bot.generate            -> data/today.json を出力
環境変数: ANTHROPIC_API_KEY, (任意) CLAUDE_MODEL
"""
import datetime as dt
import json
import os
import random
import re
from collections import Counter
from pathlib import Path

import yaml

from bot.characters import COMMON, EMOTIONS, PROPS

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data" / "history.json"
TODAY = ROOT / "data" / "today.json"

TYPES = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
         "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]
MAX_ROLE, MAX_ACTION, MAX_VOICE, MAX_REPLY, MAX_CHEAT = 9, 18, 12, 12, 12   # 画像に1行で収まる文字数

# 抽象語を禁止して「見える行動」に寄せる
BANNED = ["論理的", "感情的", "合理的", "社交的", "内向的", "外向的", "慎重", "柔軟",
          "計画的", "直感的", "共感", "冷静", "マイペース", "リーダーシップ", "傾向"]

SYSTEM = f"""あなたはInstagramアカウント「職場の16タイプ図鑑」の構成作家です。
形式は「社内チャットに、同僚16人の本音が全員宛てに誤爆する」。主語はMBTIではなく「職場にいる人」です。
16タイプ(INTJなど4文字)は小さなタグで、読者はタイプを知らなくても「あの人だ」と分かるように書きます。

# 文面のルール(最重要)
- role(役名)は、その場面での行動から付けた呼び名。「〜する人」「〜な人」の形(例: 議事録に逃げる人、締めたがる人)。
- action(行動)は周りから見える建前。カメラに映る動作か、口から出るセリフだけ。性格の説明は書かない。
- voice(本音)は行動と逆向きの本心。行動の言い換え・理由の説明・同じ方向の感想は禁止。
  良い例: 行動「誰も頼んでないのに議事録を取る」→本音「発言しない分の免罪符です」
  良い例: 行動「『意見が出そろいましたね』と締める」→本音「沈黙は同意とみなす」
  悪い例: 行動「時計を何度も見る」→本音「もう7分押している」(同じ方向の説明)
- 読者が特定の同僚・上司・自分の顔を思い浮かべて、DMで送りたくなる行を目指す。「わかる」止まりの平凡な行は書き直す。
- 全員を有能な良い人に描かない。本人が「バレた…」と苦笑いする自虐や小さな毒を多めに。
  ただし他人から見下す書き方はしない。能力・性別・年齢・病気をネタにしない。実在の企業名・人名は出さない。
- 16行で同じ型のオチを3つ以上作らない。同じ数字は全体で2回まで。数字で落とす本音は2つまで。
- 行動の語尾(〜を見る、うなずく、〜始める)は各1回まで。「『…』と〜する」型の行動は6つまで。
- 次の語は使用禁止: {"、".join(BANNED)}
- 25〜34歳の会社員が実際に使う言葉で。古い小道具やネット掲示板調の語尾は使わない。
- 「田中さん」を毎回どこかに1〜2回登場させる(固定の登場人物)。

# 演出のルール
- hot: 16人のうち一番笑える4人だけtrue(主役として1人1枚で大きく見せる)。
- prop: 主役の持ち物(省略可)。場面に合うときだけ次から選ぶ: {" / ".join(PROPS)} / none
- emotion: 本音を言っている時の顔: {" / ".join(EMOTIONS)}
  (sweat=焦り, blank=虚無の半目, sparkle=キラキラ, flat=じと目, angry=イラッ, cry=号泣, smug=ドヤ, dead=×目, shock=ガーン, sleepy=うとうと)
  文面に合うものを選び、全体で6種類以上使う。主役はsmug以外にする(建前の顔がsmugのため)。
- cover.type: 表紙に出す人。本音が文脈なしで刺さる人を、主役(hot)以外から選ぶ。
- replies: 主役4人と表紙の人、計5人それぞれへの、別の人からのツッコミ返信。本音を受けて一言で落とす。ここが一番の笑いどころ。
- events: 「部長」の動きを伝えるシステム通知6本。入室から始まり、だんだん不穏になる(例: 部長 が入室しました → 部長 が入力中… → 既読 16（部長を含む） → 部長 がスクショを撮りました)。毎回ちがう展開にする。
- boss_line: 部長だけのページで言う決めゼリフ。通知の伏線を回収して落とす。
- question: この場面についての二択。意見が割れて、答えることが立場表明になるもの。
- cheat: 保存用の実用ページ。この場面で「各タイプにこう声をかけると動く」一言を16人分。無難な一般論は避け、明日そのまま使える言い回しにする。

# 文字数(厳守)
role {MAX_ROLE} / action {MAX_ACTION} / voice {MAX_VOICE} / 返信 {MAX_REPLY} / cheatの一言 {MAX_CHEAT} 文字以内

出力はJSONのみ。前置きやコードブロック記号は不要。"""

PROMPT = """瞬間: 「{moment}」(カテゴリ: {category})

次のJSONを返してください:
{{"cover": {{"headline": "場面を一言で(14文字以内、句点で終える。例: 会議で10秒、誰も喋らない。)", "type": "表紙に出すタイプ(hot以外)"}},
 "items": [{{"type": "INTJ", "role": "...", "action": "...", "voice": "...", "emotion": "flat", "hot": false}},
           {{"type": "INTP", "role": "...", "action": "...", "voice": "...", "emotion": "sleepy", "hot": true, "prop": "none"}},
           ... 16タイプ全部、この順: {types}],
 "replies": [{{"to": "返信先のタイプ", "from": "返信するタイプ", "text": "..."}}, ... 主役4人と表紙の人あて、計5つ],
 "events": ["部長 が入室しました", "...", "...", "...", "...", "..."],
 "boss_line": "部長の決めゼリフ(16文字以内)",
 "question": {{"text": "二択の問い(12文字以内)", "a": "選択肢A(5文字以内)", "b": "選択肢B(5文字以内)",
              "cat_a": "Aを象徴するタイプ", "cat_b": "Bを象徴するタイプ"}},
 "cheat": {{"title": "保存用ページの見出し(20文字以内)", "items": {{"INTJ": "...", ... 16タイプ全部}}}},
 "caption": "キャプション本文(120〜200文字。冒頭1行で場面を提示し、最後は二択の問いで締める)"}}"""

HASHTAGS = "#16タイプ #性格診断 #職場あるある #会社員あるある #仕事あるある #{tag}"
DISCLAIMER = "※16タイプ性格分類をもとにした「あるある」ネタです。公式のMBTI®検査とは異なります。"


def load_history() -> list:
    return json.loads(HISTORY.read_text()) if HISTORY.exists() else []


def pick(history: list, today: dt.date) -> dict:
    """未使用ネタを1つ選ぶ。全部使い切ったら2周目に入る。前回と同じカテゴリは避ける。"""
    scenes = yaml.safe_load((ROOT / "content" / "scenes.yaml").read_text())
    used = {h["key"] for h in history}
    pool = [{"format": "all16", "category": c, "moment": m, "key": f"16|{m}"}
            for c, ms in scenes["moments"].items() for m in ms]
    last = next((h.get("category") for h in reversed(history) if h.get("category")), None)
    if any(p["category"] != last for p in pool if p["key"] not in used):
        pool = [p for p in pool if p["category"] != last]
    fresh = [p for p in pool if p["key"] not in used] or pool
    return random.Random(today.isoformat()).choice(fresh)


def validate(post: dict) -> list:
    errs = []
    items = post.get("items", [])
    if [i.get("type") for i in items] != TYPES:
        return ["itemsは16タイプを指定順で"]
    by = {i["type"]: i for i in items}
    for i in items:
        t = i["type"]
        for key, mx in (("role", MAX_ROLE), ("action", MAX_ACTION), ("voice", MAX_VOICE)):
            if not 1 <= len(i.get(key, "")) <= mx:
                errs.append(f"{t}: {key}は{mx}文字以内")
        if not i.get("role", "").endswith("人"):
            errs.append(f"{t}: roleは「〜人」で終える")
        if i.get("emotion") not in EMOTIONS:
            errs.append(f"{t}: emotionは{EMOTIONS}のどれか")
    if errs:
        return errs
    hots = [t for t in TYPES if by[t].get("hot") is True]
    if len(hots) != 4:
        errs.append("hotはちょうど4人")
    for t in hots:
        if by[t].get("prop", "none") not in PROPS + ["none"]:
            errs.append(f"{t}: propは{PROPS + ['none']}のどれか(省略可)")
        if by[t]["emotion"] == "smug":
            errs.append(f"{t}: 主役のemotionはsmug以外")
    if len({i["emotion"] for i in items}) < 6:
        errs.append("emotionは6種類以上使う")
    for key in ("role", "action", "voice"):
        if len({i[key] for i in items}) < 16:
            errs.append(f"{key}が重複")

    blob = json.dumps(post, ensure_ascii=False)
    errs += [f"禁止語: {w}" for w in BANNED if w in blob]
    text = "".join(i["action"] + i["voice"] for i in items)
    for num, c in Counter(re.findall(r"\d+", text)).items():
        if c >= 3:
            errs.append(f"数字「{num}」が{c}回(2回まで)")
    if sum(bool(re.search(r"\d", i["voice"])) for i in items) > 2:
        errs.append("数字で落とす本音は2つまで")
    for tail in ("を見る", "うなずく", "始める"):
        if sum(i["action"].endswith(tail) for i in items) > 1:
            errs.append(f"行動の語尾「{tail}」は1回まで")
    if sum(i["action"].startswith("「") for i in items) > 6:
        errs.append("「…」で始まる行動は6つまで")
    if "田中" not in blob:
        errs.append("田中さんが登場していない")

    cov = post.get("cover") or {}
    if not 1 <= len(cov.get("headline", "")) <= 14:
        errs.append("cover.headlineは14文字以内")
    if cov.get("type") not in TYPES or cov.get("type") in hots:
        errs.append("cover.typeはhot以外の16タイプ")
    reps = post.get("replies") or []
    if sorted(r.get("to", "") for r in reps) != sorted(hots + [cov.get("type", "")]):
        errs.append("repliesは主役4人と表紙の人あてに1つずつ、計5つ")
    for r in reps:
        if r.get("from") not in TYPES or r.get("from") == r.get("to") or not 1 <= len(r.get("text", "")) <= MAX_REPLY:
            errs.append(f"返信({r.get('to')}宛)はfromが別タイプで{MAX_REPLY}文字以内")
    ev = post.get("events") or []
    if len(ev) != 6 or not all(isinstance(v, str) and "部長" in v and len(v) <= 18 for v in ev):
        errs.append("eventsは6本、全部に部長を入れ、各18文字以内")
    if not 1 <= len(post.get("boss_line", "")) <= 16:
        errs.append("boss_lineは16文字以内")
    q = post.get("question") or {}
    if not (1 <= len(q.get("text", "")) <= 12 and 1 <= len(q.get("a", "")) <= 5 and 1 <= len(q.get("b", "")) <= 5
            and q.get("cat_a") in TYPES and q.get("cat_b") in TYPES):
        errs.append("questionはtext12文字以内、a/b各5文字以内、cat_a/cat_bは16タイプ")
    ch = post.get("cheat") or {}
    ci = ch.get("items") or {}
    if not 1 <= len(ch.get("title", "")) <= 20 or sorted(ci) != sorted(TYPES):
        errs.append("cheatはtitle20文字以内、itemsは16タイプ全部")
    elif not all(1 <= len(v) <= MAX_CHEAT for v in ci.values()):
        errs.append(f"cheatの一言は{MAX_CHEAT}文字以内")
    return errs


def call_claude(prompt: str) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"),
        max_tokens=6000, system=SYSTEM,
        messages=[{"role": "user", "content": prompt}])
    text = "".join(b.text for b in msg.content if b.type == "text")
    return json.loads(re.search(r"\{.*\}", text, re.S).group(0))


def main():
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    history = load_history()
    topic = pick(history, today)
    prompt = PROMPT.format(types=" ".join(TYPES), **topic)

    feedback = ""
    for attempt in range(5):
        post = call_claude(prompt + feedback)
        errs = validate(post)
        if not errs:
            break
        feedback = "\n\n前回の出力は次の点で不合格でした。直して全体を出し直してください:\n- " + "\n- ".join(errs)
    else:
        raise SystemExit(f"検証に通らず中止(投稿しません): {errs}")

    nxt = pick(history + [topic], today + dt.timedelta(days=1))          # 締めページの次回予告
    post["next"] = nxt["moment"]
    legend = " / ".join(f"{t}＝{COMMON[t]}" for t in TYPES)              # 通称で探す人向けの早見表
    tag = topic["category"].replace("・", "")
    post["caption"] = f'{post["caption"]}\n\n【タイプ早見】{legend}\n\n{DISCLAIMER}\n\n{HASHTAGS.format(tag=tag)}'
    post.update(topic, date=today.isoformat(), title=post["cover"]["headline"])
    TODAY.write_text(json.dumps(post, ensure_ascii=False, indent=2))
    print(f'OK: {post["title"]} ({topic["key"]})')


if __name__ == "__main__":
    main()

"""今日のネタを選び、Claude APIで「いる、こういう人。」形式の投稿内容(JSON)を作る。

1投稿=1タイプの「職場にいる人」。本人の言い分と周りの本音をぶつけ、二択で締める。
usage: python -m bot.talk_generate       -> data/today.json を出力
環境変数: ANTHROPIC_API_KEY, (任意) CLAUDE_MODEL
"""
import datetime as dt
import json
import os
import random
import re
from pathlib import Path

import yaml

from bot.characters import COMMON, EMOTIONS, PROPS
from bot.generate import DISCLAIMER, HASHTAGS, TYPES, load_history

ROOT = Path(__file__).resolve().parent.parent
TODAY = ROOT / "data" / "today.json"
FORMAT = "talk"
BANNED = ["どちらでも", "どっちも", "場合による", "ケースバイケース", "人それぞれ", "無能", "クズ", "最低", "使えない", "老害"]

SYSTEM = """あなたはInstagramアカウント「職場の16タイプ図鑑」の構成作家です。
形式は「いる、こういう人。」。職場にいる1人の行動を漫画のコマで見せ、本人の言い分と周りの本音をぶつけて、最後に読者へ二択を聞きます。
狙いは2つだけ: 読者が「いるいる、こういう人」と思うこと。コメント欄でAかBかの議論が起きること。

# 必ず守ること
- 主役は悪者にしない。本人の言い分にも、周りの本音にも筋が通っていること。片方が明らかに正しい話は不合格。
- 両方の側に「数字で分かる損得」を入れる(例: 私が40分謝りました / 私も18:10に帰れてます)。
- 場面は具体的に。時刻・人数・回数・金額・セリフを使い、「コミュニケーション」「価値観」「多様性」のような抽象語は使わない。
- 二択は「その場で読者が取る行動」にする(呼び戻す / 朝まで待つ)。制度や方針の是非を聞かない。第三の選択肢や「人それぞれ」に逃げない。
- タイプと行動のつながりを why で一言で言う。断定せず「〜に多いと言われる」程度の距離感で、人格を決めつけない。
- 特定の人を傷つける言葉、性別・年齢・国籍などの属性いじりは書かない。
- 出力はJSONだけ。前置きも説明も書かない。"""

PROMPT = """# 今日のネタ
主役のタイプ: {type}({common})
こういう人: {title}
場面のヒント: {scene}

# 各項目の役割と文字数(画像に収めるため厳守)
- title: 表紙の題名を2行で。各9文字以内。2行目は「人」で終える(例: ["18:00:00に", "席を立つ人"])
- time: 表紙の左上に出す時刻や回数の札。8文字以内(例: "18:00:00")
- sfx: 主役の動きの擬音。カタカナ5文字以内(例: "ガタッ")
- line: 主役のひとこと。8文字以内(例: "お先です")
- hero: 表紙の主役の絵。emotion は {emotions} から。prop は {props} / none から(場面に合うときだけ)。pose は "walk"(立ち去る・歩く)か ""。
- react: 周りの反応の擬音。4文字以内(例: "えっ")
- event: 直後に起きる出来事。time 6文字以内、lines は1〜2行で各7文字以内、sfx 6文字以内
- around: 周りの本音を3人分。type は主役以外の16タイプで3人とも別。role は立場(7文字以内。例: 隣の席の人、上司、後輩)。
  text は2行、各13文字以内。3人のうち2人は主役に困っている側、1人は主役に助けられている側にする。2人以上の text に数字を入れる。
- self: 本人の言い分を2つ。text は1〜2行、各13文字以内。1つ以上に数字を入れる。emotion も付ける。
- why: このタイプに多いと言われる理由を2行で。各11文字以内(例: ["決めた線は", "1秒も動かさない"])
- question: 二択の問いを2行で。各16文字以内。1行目は状況、2行目は「あなたが上司なら？」のように読者の立場を決めて「？」で終える
- a / b: 二択。label 6文字以内。arg はその選択の言い分を2行、各12文字以内。type と emotion は、その選択を取りそうなタイプ(16タイプ、主役以外)と顔。
- caption: 投稿本文。1行目で場面を言い切り、2〜3行で両方の言い分を紹介し、最後に「AかBか、理由を一言でコメント」と促す。200文字以内。ハッシュタグは書かない。

emotion の意味: sweat=焦り, blank=虚無の半目, sparkle=キラキラ, flat=じと目, angry=イラッ, cry=号泣, smug=ドヤ, dead=×目, shock=ガーン, sleepy=うとうと, normal=ふつう

# 出力形式
{{"title": ["...", "...人"], "time": "...", "sfx": "...", "line": "...",
 "hero": {{"emotion": "flat", "prop": "bag", "pose": "walk"}}, "react": "...",
 "event": {{"time": "18:03", "lines": ["...", "..."], "sfx": "..."}},
 "around": [{{"type": "ESFJ", "emotion": "sweat", "role": "...", "text": ["...", "..."]}}, {{...}}, {{...}}],
 "self": [{{"emotion": "flat", "text": ["...", "..."]}}, {{"emotion": "smug", "text": ["..."]}}],
 "why": ["...", "..."],
 "question": ["...", "...？"],
 "a": {{"label": "...", "arg": ["...", "..."], "type": "ENTJ", "emotion": "angry"}},
 "b": {{"label": "...", "arg": ["...", "..."], "type": "ENFP", "emotion": "sparkle"}},
 "caption": "..."}}"""


def topics() -> list:
    data = yaml.safe_load((ROOT / "content" / "topics.yaml").read_text())["topics"]
    return [dict(t, category=c, format=FORMAT, key=f'talk|{t["title"]}') for c, ts in data.items() for t in ts]


def pick(history: list, today: dt.date) -> dict:
    """未使用ネタを1つ選ぶ。使い切ったら2周目。直前と同じタイプ・同じ分類は避ける。"""
    pool, used = topics(), {h.get("key") for h in history}
    last = history[-1] if history else {}
    fresh = [p for p in pool if p["key"] not in used] or pool
    better = [p for p in fresh if p["category"] != last.get("category") and p["type"] != last.get("type")]
    return random.Random(today.isoformat()).choice(better or fresh)


def _lines(v, n_min, n_max, mx):
    return isinstance(v, list) and n_min <= len(v) <= n_max and all(isinstance(s, str) and 1 <= len(s) <= mx for s in v)


def _digit(v):
    return bool(re.search(r"[0-9０-９]", "".join(v)))


def validate(post: dict, hero: str) -> list:
    errs = []
    blob = json.dumps(post, ensure_ascii=False)
    errs += [f"使えない言葉: {w}" for w in BANNED if w in blob]

    t = post.get("title")
    if not _lines(t, 2, 2, 9) or not t[1].endswith("人"):
        errs.append("titleは2行、各9文字以内、2行目は「人」で終える")
    for key, mx in (("time", 8), ("sfx", 5), ("line", 8), ("react", 4)):
        if not 1 <= len(post.get(key) or "") <= mx:
            errs.append(f"{key}は{mx}文字以内")
    h = post.get("hero") or {}
    if h.get("emotion") not in EMOTIONS or h.get("prop", "none") not in PROPS + ["none"] or h.get("pose", "") not in ("", "walk"):
        errs.append(f"heroはemotion={EMOTIONS}, prop={PROPS + ['none']}, pose=walkか空")
    ev = post.get("event") or {}
    if not (1 <= len(ev.get("time") or "") <= 6 and _lines(ev.get("lines"), 1, 2, 7) and 1 <= len(ev.get("sfx") or "") <= 6):
        errs.append("eventはtime6文字以内、linesは1〜2行で各7文字以内、sfx6文字以内")

    ar = post.get("around") or []
    if len(ar) != 3:
        errs.append("aroundはちょうど3人")
    else:
        ts = [a.get("type") for a in ar]
        if any(x not in TYPES or x == hero for x in ts) or len(set(ts)) != 3:
            errs.append("aroundのtypeは主役以外の16タイプで、3人とも別")
        for a in ar:
            if a.get("emotion") not in EMOTIONS or not 1 <= len(a.get("role") or "") <= 7 or not _lines(a.get("text"), 2, 2, 13):
                errs.append(f'around({a.get("role")}): emotionは既定のもの、role7文字以内、textは2行で各13文字以内')
        if sum(_digit(a.get("text") or []) for a in ar) < 2:
            errs.append("aroundは2人以上のtextに数字を入れる")
    se = post.get("self") or []
    if len(se) != 2 or not all(s.get("emotion") in EMOTIONS and _lines(s.get("text"), 1, 2, 13) for s in se):
        errs.append("selfは2つ、emotion付き、textは1〜2行で各13文字以内")
    elif not any(_digit(s["text"]) for s in se):
        errs.append("selfの1つ以上に数字を入れる")
    if not _lines(post.get("why"), 1, 2, 11):
        errs.append("whyは1〜2行、各11文字以内")

    q = post.get("question")
    if not _lines(q, 2, 2, 16) or not q[1].endswith("？"):
        errs.append("questionは2行、各16文字以内、2行目は「？」で終える")
    labels = []
    for k in ("a", "b"):
        c = post.get(k) or {}
        labels.append(c.get("label"))
        if not (1 <= len(c.get("label") or "") <= 6 and _lines(c.get("arg"), 1, 2, 12)
                and c.get("type") in TYPES and c.get("type") != hero and c.get("emotion") in EMOTIONS):
            errs.append(f"{k}: label6文字以内、argは1〜2行で各12文字以内、typeは主役以外の16タイプ、emotion付き")
    if labels[0] == labels[1]:
        errs.append("aとbのlabelは別のもの")
    cap = post.get("caption") or ""
    if not 1 <= len(cap) <= 200 or "#" in cap or "＃" in cap:
        errs.append("captionは200文字以内、ハッシュタグなし")
    elif "A" not in cap or "B" not in cap:
        errs.append("captionの最後でAかBかのコメントを促す")
    return errs


def call_claude(prompt: str) -> dict:
    import anthropic
    msg = anthropic.Anthropic().messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"),
        max_tokens=3000, system=SYSTEM,
        messages=[{"role": "user", "content": prompt}])
    text = "".join(b.text for b in msg.content if b.type == "text")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("JSON が見つからない")
    return json.loads(m.group(0))


def finish(post: dict, topic: dict, nxt: dict, today: dt.date) -> dict:
    """検証済みの内容に、次回予告・タイプ表記・注記・ハッシュタグを足す。"""
    hero = topic["type"]
    post["type"] = hero
    post["next"] = nxt["title"]
    post["caption"] = (f'{post["caption"]}\n\n【今回の主役】{hero}＝{COMMON[hero]}(に多いと言われるタイプ)\n\n'
                       f'{DISCLAIMER}\n\n{HASHTAGS.format(tag=hero)} #{COMMON[hero]}')
    lines = post["title"]
    post.update({k: topic[k] for k in ("key", "format", "category")}, date=today.isoformat(),
                title="".join(lines), title_lines=lines)
    return post


def main():
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    history = load_history()
    topic = pick(history, today)
    prompt = PROMPT.format(common=COMMON[topic["type"]], emotions=" / ".join(EMOTIONS), props=" / ".join(PROPS),
                           **{k: topic[k] for k in ("type", "title", "scene")})
    feedback = ""
    for _ in range(5):
        try:
            post = call_claude(prompt + feedback)
        except ValueError as e:  # JSONDecodeError も含む
            errs = [f"JSON として読めない出力でした({e})。文字列の中では \" を使わず「」を使い、JSON だけを出力してください"]
            print("NG:", errs)
            feedback = "\n\n前回の出力は次の点で不合格でした。直して全体を出し直してください:\n- " + "\n- ".join(errs)
            continue
        errs = validate(post, topic["type"])
        if errs:
            print("NG:", errs)
        if not errs:
            break
        feedback = "\n\n前回の出力は次の点で不合格でした。直して全体を出し直してください:\n- " + "\n- ".join(errs)
    else:
        raise SystemExit(f"検証に通らず中止(投稿しません): {errs}")

    nxt = pick(history + [topic], today + dt.timedelta(days=1))
    post = finish(post, topic, nxt, today)
    TODAY.parent.mkdir(parents=True, exist_ok=True)
    TODAY.write_text(json.dumps(post, ensure_ascii=False, indent=2))
    print(f'OK: {post["title"]} ({topic["key"]})')


if __name__ == "__main__":
    main()

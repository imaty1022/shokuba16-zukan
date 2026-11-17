# 職場の16タイプ図鑑 — Instagram自動投稿

毎日20:31(JST)に、ネタ選択 → Claudeで文面生成 → 画像化 → Instagramへカルーセル投稿まで自動で行う。

## 流れ
1. `bot/generate.py` — `content/scenes.yaml` から未使用の「瞬間」を1つ選び、Claude APIで文面を生成。文字数・禁止語・ネタや数字の重複・表情の重複などを検証し、通らなければ最大5回まで作り直し、それでも不合格なら投稿しない。
2. `bot/render.py` — 1080×1350のJPEGを6枚作る。
3. `bot/publish.py` — Instagram APIでカルーセル投稿し、`data/history.json` に記録。

## 投稿形式「本音チャット誤爆」(全10枚)
社内チャットに、同僚16人の本音が全員宛てに誤爆する設定。主語は「職場にいる人」(役名)で、4文字のタイプは小さなタグ。
- 01 表紙: 誤爆した本音(特大) → 別の人のツッコミ → 発言した猫の顔。下帯に16人の索引。
- 主役ページ×4: 1人1枚。役名 / 建前の顔と行動 → 本音の全身イラスト(小道具つき) / 本音 → ツッコミ返信の2コマ。
- 一覧ページ×2: 残り12人(役名、行動、本音)。
- 各ページ下に「部長」のシステム通知が進み、部長だけの1枚でオチ。
- 保存用ページ: この場面で各タイプにかける一言を16人分。
- 締め: 二択のコメント投票、次回予告、フォロー誘導。
- チャンネル名と配色は投稿カテゴリ(8種)ごとに変わる。

`samples/final/` に見本(01〜10.jpg、一覧は sheet.jpg)。`python -m bot.render samples/all16.json samples/out` で再生成できる。

## 手描きテイスト
画像生成AIは使わず、コード描画に手描きの質感を足している。
- 猫: 色の境目を太さの揺れるペン線にし、塗りは線から少しズラして色ムラを乗せる(`bot/characters.py` の `handdrawn`)。
- 文字: 手書き風フォント2種を同梱(`assets/fonts/`。Mochiy Pop One=見出し、Yusei Magic=本文。どちらもSIL OFLで商用利用可、ライセンス文書も同梱)。
  投稿にフォントに無い文字が含まれる日は、その投稿だけ通常の書体(Noto Sans CJK)で描く。
- ページ全体: わずかに歪ませて定規の直線をなくし、紙のざらつきを乗せる(`bot/render.py` の `handify`)。
- 1投稿(10枚)の生成に約40秒かかる。

## 採点基準と結果
- `experiments/rubric.md` … 制作チェック用(20項目)。作り込みの抜けを確認する基準で、点は甘く出る。
- `experiments/rubric_buzz.md` … 「バズるか」を5人の読者像で判定する厳しい基準(100点、40=埋もれる/60=フォロワー内で好反応/75=発見タブ級)。
  この基準では5回作り直して 49→52→51→50→52 点で頭打ち。毎回残る減点は次の3つ:
  1. MBTIを見飽きた人と、MBTIを知らない人が表紙で止まらない
  2. 5人中2人しか誰かに送らない
  3. コード描画の猫が「素材っぽい」
  採点はAIによる推定で、実際の反応とは別物。投稿後は送信数・保存数・リーチで判断すること。

## 新方針の試作「いる、こういう人。」(1投稿=1タイプ、共感と議論を狙う)
`experiments/talk.py` に試作、`experiments/rubric_talk.md` に採点基準(共感40点/議論40点/届き方20点、8人の読者役で判定)。
見本は `samples/talk_best/`(T5_01〜05.jpg が現時点の最良案、T2 は比較用)。**本番の自動投稿にはまだ組み込んでいない。**

構成(5枚): 表紙(場面の絵+行動を一言で) → 観察記録(時刻つきの行動4つ) → 周りの本音(3人) → 本人の言い分(3つ+決め台詞) → 二択の問い。

採点で分かったこと(同じ回の中での比較。2人の採点役が一致したものだけ):
- 見せ方は「本人の言い分 vs 周りの本音」が「2人のすれ違い」「職場裁判」より上。裁判は当事者が黙る。
- 反対側に数字つきの実害を入れ、表紙を場面に合う絵にすると約10点上がる(T5とT2の差)。
- 題材は「誰の職場にもいて、世間の正解が決まっていない」ものが強い。定時退社は飲み会不参加より約10点上。
- 下がる要因: 第3の選択肢、制度論の問い、片方が明らかに正しい設定、何の話か一瞬で分からない表紙。
- 毎回残る弱点: タイプと行動の結びつき、MBTIを見飽きた人と人事役が動かない。

注意: 同じ画像を別の回に採点すると73点→56点と動いた。絶対値は±10点ぶれるので、点数は同じ回の中の比較にだけ使うこと。

## 未実装
`experiments/v2.py` に別形式(ランキング、1タイプの非公開メモ)の描画コードが残っているが、自動生成には組み込んでいない。
`content/scenes.yaml` の `timelines` も現在は未使用。

## セットアップ(手作業が必要なのはここだけ)
1. Instagramでアカウントを作り、プロアカウント(クリエイター)に切り替える。
2. Meta for Developersでアプリを作成し、ビジネスポートフォリオにつなぐ。ユースケース「Instagramでメッセージとコンテンツを管理」の
   「API setup with Unified login」で設定を作り(権限 `instagram_basic`, `instagram_content_publish`)、
   自分のアカウントを Instagram テスターにしてシステムユーザーアクセストークン(無期限)を発行。
   (新しいアプリでは「Instagramログイン」のAPI設定は選べない。2026-11 時点)
3. このフォルダを **公開** GitHubリポジトリにpush(Instagramが画像をURLから取得するため。非公開にしたい場合は `IMAGE_BASE_URL` を別の公開ストレージに向ける)。
4. リポジトリの Settings → Secrets に登録:
   - `ANTHROPIC_API_KEY`
   - `IG_USER_ID` (InstagramのユーザーID)
   - `IG_ACCESS_TOKEN` (システムユーザーアクセストークン。`python -m bot.publish --whoami` で IG_USER_ID を確認できる)
5. Actionsタブで `daily-post` を手動実行して初回投稿を確認。

## ローカルで試す
```
pip install -r requirements.txt
python -m bot.render samples/all16.json samples/out     # APIキーなしで画像だけ確認(numpyも必要)
ANTHROPIC_API_KEY=... python -m bot.generate && python -m bot.render
```

## 調整ポイント
- ネタを足す: `content/scenes.yaml` に行を追加(場所・時刻・数字・セリフのどれかを入れる)。
- 文体・禁止語: `bot/generate.py` の `SYSTEM` と `BANNED`。
- 投稿時刻: `.github/workflows/daily.yml` の cron(UTC)。
- モデル: 環境変数 `CLAUDE_MODEL`。

## 未検証の箇所
Claude API呼び出しとInstagram API呼び出しは、キーがない環境で書いたため実行確認していない。
初回は `workflow_dispatch` で手動実行し、エラーが出たらログを確認すること。
APIバージョンは `IG_API_VERSION` で変更できる。

## キャラクター
`bot/characters.py` が16匹の猫をコードで描く(毛並み=タイプ別、E/I=口と目線、F=ほっぺ、J=ネクタイ、P=アホ毛、小道具=タイプ別)。表情は11種、タイプ固定の小物つき。表記は「4文字＋独自の呼び名」、通称はキャプションの早見表に入れる。手描き素材への差し替えは `assets/README.md` を参照。`python -m bot.characters` で一覧を `samples/characters.png` に出力。小道具は `PROP` と `p_*` 関数で差し替え可能。

## キャラクター（ちび社員）

標準の絵柄は `bot/chibi.py` の「ちび社員」です（16タイプ＋部長、表情11種、歩きポーズあり）。

- 一覧の出力: `python -m bot.chibi` → `samples/characters.jpg`, `samples/emotions.jpg`
- 呼び出し: `characters.draw(type, height, emotion, prop, pose)`。持ち物は場面用の `bag` / `laptop` / `phone` だけ（省略で手ぶら）。`pose="walk"` で歩く
- タイプ固定の小道具は廃止。画像に出すタイプ名は一般的な通称（建築家、巨匠など）
- 旧絵柄に戻す: 環境変数 `CHAR_STYLE=classic`
- `assets/chars/{TYPE}_{emotion}.png` を置けば、そちらが優先されます
- 絵柄の比較試作は `experiments/chars.py`

## 本番の形式:「いる、こういう人。」（1投稿1タイプ・5枚）

毎日の自動投稿はこの形式です（`.github/workflows/daily.yml` が `bot.talk_generate` → `bot.talk_render` → `bot.publish` を実行）。

| 枚 | 内容 |
|---|---|
| 1 | 表紙: 漫画コマで場面を見せる（時刻の札、擬音、主役、周りの反応、直後の出来事） |
| 2 | 周りの本音: 3人（困っている側2人、助かっている側1人） |
| 3 | 本人の言い分2つ ＋ そのタイプに多いと言われる理由 |
| 4 | 二択 A / B |
| 5 | 締め: コメント誘導、同僚に送る、次回予告、注記 |

- ネタ帳: `content/topics.yaml`（34本。行を足せば増える）
- 生成と検証: `bot/talk_generate.py`（文字数、数字の有無、二択の形、使えない言葉を検査。5回まで出し直し、通らなければ投稿しない）
- 描画: `bot/talk_render.py`。見本は `python -m bot.talk_render samples/talk.json samples/talk_final`
- 以前の16人形式（`bot/generate.py` / `bot/render.py`）は残してあり、ワークフローの2行を戻せば使えます

**未確認**: Claude API と Instagram API の呼び出しは、鍵がないため一度も実行していません。生成は応答を差し替えた空実行と、手書きの見本データでの検証・描画までを確認しています。

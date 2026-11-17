"""data/today.json と posts/<日付>/*.jpg をInstagramにカルーセル投稿する。

usage: python -m bot.publish           投稿
       python -m bot.publish --whoami  トークンから見えるIGアカウントのIDを出す(IG_USER_ID の確認用)
環境変数: IG_USER_ID, IG_ACCESS_TOKEN, IMAGE_BASE_URL (画像を公開しているURLの親。末尾スラッシュなし)
トークンは Meta の統合ログイン(Unified login)で発行したシステムユーザーアクセストークン。無期限なので更新は不要。
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

from bot.generate import HISTORY, ROOT, TODAY, load_history

API = f'https://graph.facebook.com/{os.environ.get("IG_API_VERSION", "v26.0")}'


def call(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    r = requests.request(method, f"{API}/{path}", params=params, timeout=60)
    if not r.ok:
        raise SystemExit(f"Instagram API error {r.status_code}: {r.text}")
    return r.json()


def wait_ready(container_id):
    for _ in range(30):
        status = call("GET", container_id, fields="status_code")["status_code"]
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container {container_id}: {status}")
        time.sleep(5)
    raise SystemExit(f"container {container_id}: timeout")


def publish():
    post = json.loads(TODAY.read_text())
    history = load_history()
    if any(h["date"] == post["date"] for h in history):
        raise SystemExit("今日はすでに投稿済み")          # 二重投稿防止
    user = os.environ["IG_USER_ID"]
    base = os.environ["IMAGE_BASE_URL"]
    images = sorted((ROOT / "posts" / post["date"]).glob("*.jpg"))
    children = []
    for img in images:
        url = f'{base}/posts/{post["date"]}/{img.name}'
        cid = call("POST", f"{user}/media", image_url=url, is_carousel_item="true")["id"]
        wait_ready(cid)
        children.append(cid)
    parent = call("POST", f"{user}/media", media_type="CAROUSEL",
                  children=",".join(children), caption=post["caption"])["id"]
    wait_ready(parent)
    media_id = call("POST", f"{user}/media_publish", creation_id=parent)["id"]

    history.append({k: post.get(k) for k in ("date", "key", "format", "category", "title")} | {"media_id": media_id})
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=1))
    print(f"published: {media_id}")


def whoami():
    pages = call("GET", "me/accounts", fields="name,instagram_business_account{id,username}")
    for page in pages.get("data", []):
        ig = page.get("instagram_business_account")
        if ig:
            print(f'{ig["id"]}  @{ig.get("username")}  (Page: {page["name"]})')
    if not any(page.get("instagram_business_account") for page in pages.get("data", [])):
        print("IGアカウントが見つからない。Meta の画面でトークン生成時に表示されるIDを使う")


if __name__ == "__main__":
    whoami() if "--whoami" in sys.argv else publish()

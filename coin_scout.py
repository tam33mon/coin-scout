#!/usr/bin/env python3
"""Coin-Scout.

eBay に新しく出品されたアンティークコインのうち、
  - 価格が 150 ドル以上
  - タイトルに「NGC」または「PCGS」を含む
ものを検知して、Discord に通知します。
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

# ====== 設定（必要ならここの数字や言葉を変えるだけでOK）======
MARKETPLACE = "EBAY_US"          # 米国サイト（価格はUSD）
MIN_PRICE = 150.0                # 下限価格（USD）
KEYWORDS = ["NGC", "PCGS"]       # このどれかを含む出品だけ通知
SEARCH_LIMIT = 50                # 1キーワードあたりの取得件数
SEEN_FILE = Path("seen.json")    # 通知済みアイテムIDの記録ファイル
MAX_SEEN = 5000                  # 記録を増やしすぎないための上限
# ==========================================================

EBAY_OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"


def get_env(name):
    """環境変数（GitHubのSecrets）を読む。無ければ止める。"""
    val = os.environ.get(name)
    if not val:
        print(f"[エラー] 環境変数 {name} が設定されていません。", file=sys.stderr)
        sys.exit(1)
    return val


def get_ebay_token(client_id, client_secret):
    """eBay APIを使うためのアクセストークンを取得する。"""
    creds = f"{client_id}:{client_secret}".encode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64.b64encode(creds).decode(),
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    r = requests.post(EBAY_OAUTH_URL, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def search_ebay(token, keyword):
    """指定キーワードで、新着順・価格下限つきで検索する。"""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE,
    }
    params = {
        "q": keyword,
        "filter": f"price:[{int(MIN_PRICE)}..],priceCurrency:USD",
        "sort": "newlyListed",
        "limit": SEARCH_LIMIT,
    }
    r = requests.get(EBAY_SEARCH_URL, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("itemSummaries") or []


def passes_filters(item):
    """価格(USD 150以上) と タイトルにNGC/PCGS を含むかを最終確認する。"""
    price = item.get("price") or {}
    try:
        value = float(price.get("value", 0))
    except (TypeError, ValueError):
        return False
    if price.get("currency") != "USD" or value < MIN_PRICE:
        return False
    title = (item.get("title") or "").upper()
    return any(kw in title for kw in KEYWORDS)


def load_seen():
    if SEEN_FILE.exists():
        try:
            return json.loads(SEEN_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []


def save_seen(seen):
    trimmed = seen[-MAX_SEEN:]  # 古いものから捨てて上限内に収める
    SEEN_FILE.write_text(json.dumps(trimmed, ensure_ascii=False))


def notify_discord(webhook_url, item):
    """1件の出品をDiscordに送る（画像つきの埋め込みカード）。"""
    title = item.get("title", "(タイトル不明)")
    price = item.get("price") or {}
    price_str = f"{price.get('value', '?')} {price.get('currency', '')}"
    url = item.get("itemWebUrl", "")
    image = (item.get("image") or {}).get("imageUrl")

    embed = {
        "title": title[:256],
        "url": url,
        "color": 0xF1C40F,  # 金色っぽい色
        "fields": [
            {"name": "価格", "value": price_str, "inline": True},
        ],
    }
    if image:
        embed["thumbnail"] = {"url": image}

    payload = {
        "content": "🪙 新着コインを見つけました",
        "embeds": [embed],
    }

    r = requests.post(webhook_url, json=payload, timeout=30)
    if not r.ok:
        # 通知が1件失敗しても全体は止めず、ログだけ残す
        print(f"[警告] Discord通知に失敗: {r.status_code} {r.text}", file=sys.stderr)


def main():
    client_id = get_env("EBAY_CLIENT_ID")
    client_secret = get_env("EBAY_CLIENT_SECRET")
    webhook_url = get_env("DISCORD_WEBHOOK_URL")

    token = get_ebay_token(client_id, client_secret)

    seen = load_seen()
    seen_set = set(seen)
    is_first_run = len(seen) == 0

    # 2つのキーワードで検索し、重複を除いて条件に合うものだけ残す
    found = {}
    for kw in KEYWORDS:
        for item in search_ebay(token, kw):
            item_id = item.get("itemId")
            if item_id and item_id not in found and passes_filters(item):
                found[item_id] = item

    new_items = [(iid, it) for iid, it in found.items() if iid not in seen_set]
    print(f"条件一致: {len(found)}件 / うち新規: {len(new_items)}件")

    for item_id, item in new_items:
        if not is_first_run:
            notify_discord(webhook_url, item)
            time.sleep(1)  # Discord に優しく（連続送信しすぎない）
        seen.append(item_id)

    if is_first_run:
        print("初回実行のため通知はスキップし、既存の出品を記録しました。"
              "次回以降の新着から通知します。")

    save_seen(seen)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
import os, json
from urllib.parse import urljoin
from datetime import datetime
import requests
from bs4 import BeautifulSoup

KEYWORDS = ["오피스텔"]      # 예: ["역삼","전세","신축"]
ANY_MATCH = True
SEEN_FILE = "seen.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SITES = [
    {
        "name": "예시사이트",
        "url": "https://example.com/search?q=오피스텔",  # 너의 검색결과 URL로 교체
        "item_selector": "li",
        "title_selector": "a",
        "url_selector": "a",
        "encoding": ""
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                  "Version/16.0 Mobile/15E148 Safari/604.1"
}

def load_seen():
    try:
        return json.load(open(SEEN_FILE, "r", encoding="utf-8"))
    except Exception:
        return {}

def save_seen(d):
    json.dump(d, open(SEEN_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def matches(text):
    t = (text or "").lower()
    keys = [k.lower() for k in KEYWORDS]
    return any(k in t for k in keys) if ANY_MATCH else all(k in t for k in keys)

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[경고] 텔레그램 설정 비어있음:", msg)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)

def fetch_items(site):
    r = requests.get(site["url"], headers=HEADERS, timeout=20)
    if site.get("encoding"):
        r.encoding = site["encoding"]
    elif not r.encoding:
        r.encoding = r.apparent_encoding or "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for it in soup.select(site["item_selector"]):
        t = it.select_one(site["title_selector"])
        u = it.select_one(site["url_selector"])
        if not t or not u:
            continue
        title = t.get_text(strip=True)
        href = (u.get("href") or "").strip()
        if not href:
            continue
        out.append((title, urljoin(site["url"], href)))
    return out

def run_once():
    seen = load_seen()
    changed = False
    for site in SITES:
        name = site["name"]
        already = set(seen.get(name, []))
        for title, link in fetch_items(site):
            if link not in already and matches(title):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                msg = f"[새 매물] {name}\n{title}\n{link}\n발견: {ts}"
                send_telegram(msg)
                print(msg)
                already.add(link)
                changed = True
        seen[name] = list(already)
    if changed:
        save_seen(seen)

if __name__ == "__main__":
    run_once()

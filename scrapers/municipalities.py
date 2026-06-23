# -*- coding: utf-8 -*-
"""Tier1自治体の入札・公募ページを汎用的に収集する。

設計：各サイトを個別に精密パースせず、入札公告ページ内の
「リンク＋その周辺テキスト」を全部拾い、キーワード該当だけ抽出する。
構造変更に強く保守が軽い。data/municipalities.csv の enabled=1 かつ
bid_page_url が設定された行が対象。
"""
import csv
import hashlib
import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import config

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "municipalities.csv")
UA = {"User-Agent": "Mozilla/5.0 (koubo-watch; +https://github.com/Vamos1230/koubo-watch)"}

# リンク文字列がこれらだけの場合は親要素のテキストを見る（詳細/PDF等）
GENERIC_LINK_TEXTS = {"詳細", "こちら", "PDF", "pdf", "リンク", "ダウンロード", "開く", ">>", "»"}

# 本物の入札・公募案件の目印。これを含まない一致（サイトのナビ等）は除外する
PROCUREMENT_MARKERS = ["委託", "入札", "公募", "プロポーザル", "企画提案", "募集", "公告", "調達", "見積"]

# 既に終了・結果公表のもの（新規募集ではない）は除外
CLOSED_MARKERS = ["審査結果", "選定結果", "落札結果", "入札結果", "結果について",
                  "結果の公表", "質問内容及び回答", "質問及び回答", "質問と回答", "中止",
                  "公募終了", "公募を終了", "受付終了", "募集終了", "終了しました"]


def _clean_title(text):
    """パンくず（ホーム > … > 本題）と末尾のサイト名（／○○県）を除去する。"""
    for sep in (" > ", " ＞ ", ">", "＞"):
        if sep in text:
            text = text.rsplit(sep, 1)[-1]
    # 末尾のサイト名サフィックスを除去：「…／千葉県」「…｜栃木県公式」等
    for sep in ("／", "｜", "|"):
        if sep in text:
            head, tail = text.rsplit(sep, 1)
            if len(tail) <= 14 and any(k in tail for k in ("県", "市", "町", "村", "ホームページ", "公式", "ウェブサイト")):
                text = head
    return text.strip()


def _load_targets():
    targets = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = (row.get("bid_page_url") or "").strip()
            if url and (row.get("enabled") or "").strip() == "1":
                targets.append(row)
    return targets


def _context_text(a):
    """リンクの文脈テキスト。リンク文字が汎用語なら親要素のテキストを使う。"""
    text = a.get_text(" ", strip=True)
    if not text or text in GENERIC_LINK_TEXTS or len(text) <= 3:
        parent = a.find_parent(["tr", "li", "td", "p", "div"])
        if parent:
            return parent.get_text(" ", strip=True)
    return text


def _scan_page(row, timeout=30):
    """1サイトを取得し、キーワード該当のリンクをレコード化して返す。"""
    url = row["bid_page_url"].strip()
    pref = row.get("prefecture", "")
    name = row.get("name", "")
    fmt = (row.get("list_format") or "html").strip()
    records = []
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[municipalities] {pref}{name} 取得失敗: {e}")
        return records

    if fmt == "rss":
        items = soup.find_all("item")
        for it in items:
            title = it.title.get_text(strip=True) if it.title else ""
            link = it.link.get_text(strip=True) if it.link else url
            _maybe_add(records, title, link, row)
    else:
        # 一覧ページ：各リンク＋周辺テキストを走査
        for a in soup.find_all("a", href=True):
            text = _context_text(a)
            link = urljoin(url, a["href"])
            _maybe_add(records, text, link, row)
        # 個別案件ページ：ページ自身の見出し・タイトルも候補にする
        for tag in soup.find_all(["h1", "h2", "h3", "title"]):
            _maybe_add(records, tag.get_text(" ", strip=True), url, row)
    return records


def _maybe_add(records, text, link, row):
    if not text:
        return
    matched = next((kw for kw in config.KEYWORDS if kw in text), None)
    if not matched:
        return
    # サイトのナビ等を除外：入札・公募の目印を含まない一致は捨てる
    if not any(m in text for m in PROCUREMENT_MARKERS):
        return
    # 終了・結果公表のものは除外（新規募集を優先）
    if any(m in text for m in CLOSED_MARKERS):
        return
    title = _clean_title(text)
    if len(title) < 6:  # 短すぎる断片は捨てる
        return
    pref, name = row.get("prefecture", ""), row.get("name", "")
    label = name if name == pref else f"{pref}{name}".strip()
    uid = "muni:" + hashlib.md5((label + "|" + title[:80]).encode("utf-8")).hexdigest()[:16]
    records.append({
        "source": f"{label}(入札・公募)",
        "id": uid,
        "title": title[:120],
        "organization": label,
        "deadline": "",
        "keyword": matched,
        "url": link,
    })


def _url_score(url):
    """実ページらしさのスコア。パンくずのトップ/index.html より深い実ページを優先。"""
    u = url.rstrip("/")
    if u.endswith("/index.html") or u.count("/") <= 3:
        return 0
    return u.count("/")


def fetch_tier1():
    """enabled かつ bid_page_url 設定済みの全自治体を収集。重複は実URLを優先。"""
    best = {}
    for row in _load_targets():
        for rec in _scan_page(row):
            cur = best.get(rec["id"])
            if cur is None or _url_score(rec["url"]) > _url_score(cur["url"]):
                best[rec["id"]] = rec
        time.sleep(0.5)
    all_records = list(best.values())
    print(f"[municipalities] 案件 {len(all_records)} 件ヒット")
    return all_records

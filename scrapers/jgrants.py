# -*- coding: utf-8 -*-
"""jGrants（デジタル庁 補助金電子申請システム）の公開APIから補助金を取得する。

公開API（認証不要）:
  一覧: GET https://api.jgrants-portal.go.jp/exp/v1/public/subsidies
        ?keyword=...&sort=created_date&order=DESC&acceptance=1
  詳細: GET https://api.jgrants-portal.go.jp/exp/v1/public/subsidies/id/{id}

keyword は2文字以上が必須。acceptance=1 は「現在募集中」のみ。
"""
import time
import requests

BASE = "https://api.jgrants-portal.go.jp/exp/v1/public/subsidies"
HEADERS = {"Accept": "application/json"}


def search(keyword, acceptance=1, timeout=30):
    """キーワードで補助金一覧を検索。結果（辞書）のリストを返す。"""
    params = {
        "keyword": keyword,
        "sort": "created_date",
        "order": "DESC",
        "acceptance": acceptance,
    }
    try:
        r = requests.get(BASE, params=params, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[jgrants] '{keyword}' 検索失敗: {e}")
        return []
    return data.get("result", []) or []


def fetch_all(keywords):
    """複数キーワードを横断検索し、id で重複除去した補助金リストを返す。"""
    found = {}
    for kw in keywords:
        if len(kw) < 2:
            continue
        for item in search(kw):
            sid = item.get("id")
            if not sid:
                continue
            if sid not in found:
                item["_matched_keyword"] = kw
                found[sid] = item
        time.sleep(0.5)  # API負荷軽減
    return list(found.values())


def to_record(item):
    """配信用の共通レコード形式に変換。"""
    sid = item.get("id", "")
    return {
        "source": "jGrants(補助金)",
        "id": f"jgrants:{sid}",
        "title": item.get("title") or item.get("name") or "(無題)",
        "organization": item.get("name") or item.get("target_area_search") or "",
        "deadline": item.get("acceptance_end_datetime", ""),
        "keyword": item.get("_matched_keyword", ""),
        "url": f"https://www.jgrants-portal.go.jp/subsidy/{sid}",
    }

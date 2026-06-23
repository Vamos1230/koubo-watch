# -*- coding: utf-8 -*-
"""毎日実行のエントリポイント。
  1) jGrants から補助金を全国収集
  2) (今後) Tier1自治体の入札・公募を収集
  3) キーワード絞り込み・重複除去
  4) 新着のみ配信
"""
import json
import os
import sys

import config
import delivery
from scrapers import jgrants

STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "seen.json")


def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=0)


def matches_keyword(text):
    return any(kw in text for kw in config.KEYWORDS)


def collect():
    records = []
    # --- 補助金（全国・jGrants API）---
    for item in jgrants.fetch_all(config.JGRANTS_KEYWORDS):
        records.append(jgrants.to_record(item))
    # --- 案件（Tier1自治体）は今後ここに追加 ---
    # from scrapers import municipalities
    # records += municipalities.fetch_tier1()
    return records


def main():
    dry_run = "--dry-run" in sys.argv
    seen = load_seen()
    records = collect()
    print(f"[main] 収集 {len(records)} 件（重複除去前）")

    new = [r for r in records if r["id"] not in seen]
    new = new[: config.MAX_ITEMS_PER_RUN]
    print(f"[main] 新着 {len(new)} 件")

    if dry_run:
        for r in new:
            print(f"  - [{r['source']}] {r['title']} ({r['keyword']})")
        print("[main] dry-run のため配信・状態保存はしません")
        return

    if delivery.deliver(new):
        for r in new:
            seen.add(r["id"])
        save_seen(seen)
        print("[main] 完了")


if __name__ == "__main__":
    main()

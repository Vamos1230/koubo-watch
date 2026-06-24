# -*- coding: utf-8 -*-
"""収集システムの設定。環境変数で上書き可能。"""
import os

# 検索キーワード（いずれか1つでも含めばヒット）
KEYWORDS = [
    "デジタル教育",
    "教育",
    "観光",
    "eスポーツ",
    "ｅスポーツ",
    "イースポーツ",
    "メタバース",
    "プログラミング教育",
    "ＧＩＧＡスクール",
    "GIGAスクール",
]

# jGrants（補助金）検索に使うキーワード（APIは2文字以上必須）
JGRANTS_KEYWORDS = KEYWORDS

# 配信先の選択: "chatwork" または "line"
DELIVERY = os.environ.get("DELIVERY", "line")

# Chatwork
CHATWORK_TOKEN = os.environ.get("CHATWORK_TOKEN", "")
CHATWORK_ROOM_ID = os.environ.get("CHATWORK_ROOM_ID", "")

# LINE Messaging API（push message）
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TO = os.environ.get("LINE_TO", "")  # 送信先のユーザー/グループID

# 1回の配信で送る最大件数（文字数は自動分割するので保険的な上限）
MAX_ITEMS_PER_RUN = 200

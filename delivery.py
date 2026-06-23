# -*- coding: utf-8 -*-
"""新着案件を Chatwork または LINE に配信する。"""
import requests
import config


def format_message(records):
    lines = [f"【公募・補助金 新着 {len(records)}件】\n"]
    for i, r in enumerate(records, 1):
        deadline = f"\n  締切: {r['deadline']}" if r.get("deadline") else ""
        lines.append(
            f"{i}. [{r['source']}] {r['title']}\n"
            f"  キーワード: {r['keyword']}{deadline}\n"
            f"  {r['url']}\n"
        )
    return "\n".join(lines)


def send_chatwork(text):
    if not config.CHATWORK_TOKEN or not config.CHATWORK_ROOM_ID:
        print("[delivery] Chatwork の認証情報が未設定です")
        return False
    url = f"https://api.chatwork.com/v2/rooms/{config.CHATWORK_ROOM_ID}/messages"
    r = requests.post(
        url,
        headers={"X-ChatWorkToken": config.CHATWORK_TOKEN},
        data={"body": text},
        timeout=30,
    )
    ok = r.status_code == 200
    print(f"[delivery] Chatwork 送信: {'成功' if ok else r.text}")
    return ok


def send_line(text):
    """友だち追加した全員へブロードキャスト送信（LINE_TO 不要）。
    特定ユーザー/グループに限定したい場合は LINE_TO を設定すると push 送信。"""
    if not config.LINE_TOKEN:
        print("[delivery] LINE の認証情報が未設定です")
        return False
    headers = {
        "Authorization": f"Bearer {config.LINE_TOKEN}",
        "Content-Type": "application/json",
    }
    messages = [{"type": "text", "text": text[:4900]}]
    if config.LINE_TO:
        url = "https://api.line.me/v2/bot/message/push"
        payload = {"to": config.LINE_TO, "messages": messages}
    else:
        url = "https://api.line.me/v2/bot/message/broadcast"
        payload = {"messages": messages}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    ok = r.status_code == 200
    print(f"[delivery] LINE 送信: {'成功' if ok else r.text}")
    return ok


def deliver(records):
    if not records:
        print("[delivery] 新着なし。配信スキップ。")
        return True
    text = format_message(records)
    if config.DELIVERY == "line":
        return send_line(text)
    return send_chatwork(text)

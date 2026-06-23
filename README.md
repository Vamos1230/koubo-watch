# koubo-watch — 官公庁 公募・補助金 自動収集システム

「デジタル教育 / eスポーツ / メタバース」等のキーワードを含む**補助金（全国）**と
**Tier1自治体の入札・公募案件**を毎日収集し、新着のみ Chatwork / LINE へ配信します。

## 仕組み

```
毎朝7時（GitHub Actions cron）
  ├─ jGrants公開API ─→ 補助金を全国からキーワード検索（acceptance=募集中）
  ├─ Tier1自治体スクレイパー ─→ 入札・公募の新着取得 ※今後実装
  ├─ キーワード絞り込み ＋ seen.json で重複除去
  └─ 新着のみ Chatwork / LINE へ配信
```

## 対象範囲

| 区分 | 対象 |
|------|------|
| 補助金 | **全国**（jGrants：国・都道府県・市町村を横断） |
| 案件 Tier1 | 全47都道府県 ＋ 政令市20 ＋ 栃木/茨城/群馬/千葉の全市（計174・`data/municipalities.csv`） |
| 案件 Tier2 | 人口10万人以上の市でRSS等がある自治体（今後拡張） |

## 設定

キーワードは `config.py` の `KEYWORDS` を編集。

配信先は環境変数（GitHub Secrets）で設定：

| Secret | 内容 |
|--------|------|
| `DELIVERY` | `chatwork` または `line` |
| `CHATWORK_TOKEN` | Chatwork APIトークン |
| `CHATWORK_ROOM_ID` | 配信先ルームID |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging APIのトークン |
| `LINE_TO` | 送信先ユーザー/グループID |

> 注意: 無料だった「LINE Notify」は2025年3月終了。LINE配信は Messaging API を使用。

## ローカル実行（Windowsは `py` を使用）

```bash
pip install -r requirements.txt
py main.py --dry-run   # 配信せず新着を表示
py main.py             # 収集→配信→状態保存
```

## クラウド自動実行

このリポジトリを GitHub に push → Settings > Secrets に上記を登録 →
`.github/workflows/daily.yml` が毎朝7時(JST)に自動実行。無料枠内で動作。

## 今後の拡張

- `scrapers/municipalities.py` を追加し、Tier1自治体の入札ページ/RSSを収集
- `data/municipalities.csv` の `bid_page_url` / `list_format` を埋めて対象を有効化

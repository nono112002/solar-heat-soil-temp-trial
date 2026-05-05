# サーバー設計書

最終更新: 2026-05-05

## 目的

PicoBox（区A/B/C 各台）から送られてくる温度データを **自宅内のRaspberry Pi 4** で受信・蓄積・可視化する。
クラウド（Ambient等）に依存せず、データ所有権を手元に保つ。

**設計方針: 手間を最小化する**。Dockerやコンテナ抽象化は使わず、apt install と Python で完結させる。

## 全体構成

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ PicoBox A   │  │ PicoBox B   │  │ PicoBox C   │
│ (区A 対照)  │  │ (区B 標準)  │  │ (区C 微生物)│
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │ MQTT (WiFi)    │                │
       └────────────────┴────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│  Raspberry Pi 4（自宅LAN内、Raspberry Pi OS Lite）│
│                                                   │
│  ┌──────────┐    ┌─────────────────┐             │
│  │Mosquitto │───>│ Python subscriber│            │
│  │ (apt)    │    │ (systemdサービス)│            │
│  └──────────┘    └────────┬────────┘             │
│                           │                       │
│                           ▼                       │
│                    ┌──────────────┐              │
│                    │ SQLite DB    │              │
│                    │ (1ファイル)  │              │
│                    └──────┬───────┘              │
│                           │                       │
│                           ▼                       │
│                    ┌──────────────┐              │
│                    │  Grafana     │              │
│                    │  (apt)       │              │
│                    └──────────────┘              │
└──────────────────────────────────────────────────┘
                        │
                        ▼
                 ブラウザで閲覧（Grafana）
```

## コンポーネント

| 役割 | 採用 | インストール方法 |
|---|---|---|
| MQTTブローカー | Mosquitto | `sudo apt install mosquitto mosquitto-clients` |
| MQTT購読・保存 | Python script + paho-mqtt | `pip install paho-mqtt` |
| データ保存 | SQLite | Python標準ライブラリ |
| 可視化 | Grafana | apt（Grafana公式リポジトリ） |
| サービス管理 | systemd | OS標準 |

選定理由：
- すべてOSの普通のパッケージで動く
- Pythonスクリプトは50〜100行で読み切れる
- SQLiteは1ファイルなのでバックアップが楽
- Telegrafやコンテナの設定ファイル文法を覚えなくていい

## データフロー

### Picoが送るMQTTメッセージ（既存）

`pico/main.py` の `send_mqtt()` から30分ごとに発行：

| トピック | ペイロード（JSON） | 用途 |
|---|---|---|
| `solar-heat/{zone}/{label}` | `{"time": "2026-...", "temp": 25.5}` | センサー温度 |
| `solar-heat/{zone}/power_alert` | `{"zone": "...", "bus_v": 4.0, "alert": "..."}` | 電源断アラート |

### Pythonスクリプトがやること

1. Mosquittoに接続
2. `solar-heat/+/+` をサブスクライブ
3. メッセージ受信 → JSON解析 → SQLiteに INSERT
4. systemd で常時起動・落ちたら自動再起動

### SQLiteスキーマ（案）

```sql
CREATE TABLE temperature (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,    -- ISO8601 (Picoが送る "time")
    received_at TEXT NOT NULL,  -- Pi側の受信時刻
    zone TEXT NOT NULL,
    label TEXT NOT NULL,
    temp REAL NOT NULL
);

CREATE TABLE power_alert (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at TEXT NOT NULL,
    zone TEXT NOT NULL,
    bus_v REAL,
    alert TEXT
);
```

## ネットワーク・ポート

| サービス | ポート | 公開範囲 |
|---|---|---|
| Mosquitto | 1883 | LAN内 |
| Grafana | 3000 | LAN内（ブラウザ閲覧用） |

## ディレクトリ構成（リポジトリ側）

```
server/
├── README.md                 # Pi側でのセットアップ手順
├── mqtt_logger.py            # MQTT購読 → SQLite保存
├── mqtt_logger.service       # systemdユニット定義
├── mosquitto/
│   └── mosquitto.conf        # MQTTブローカー設定
└── grafana/
    └── (ダッシュボード定義は後で追加)
```

`/etc/` 配下への配置は **シンボリックリンクで対応**（git pull で自動反映）：

```bash
sudo ln -s ~/solar-heat/server/mosquitto/mosquitto.conf /etc/mosquitto/conf.d/solar-heat.conf
sudo ln -s ~/solar-heat/server/mqtt_logger.service /etc/systemd/system/mqtt_logger.service
```

## 開発・デプロイフロー

```
[開発機（Windows）]                [Raspberry Pi 4]
                                  
git push  ─────────────────────>  git pull
                                       │
                                       ▼
                                  sudo systemctl restart mqtt_logger
                                  sudo systemctl restart mosquitto
                                       │
                                       ▼
                                  反映完了
```

## Pi側で必要なもの

| 項目 | 内容 |
|---|---|
| OS | Raspberry Pi OS Lite (64-bit) Bookworm |
| パッケージ | `mosquitto`, `python3`, `python3-paho-mqtt`, `grafana` |
| 操作 | SSH（鍵認証推奨） |

## セキュリティ方針（初期段階）

- **LAN内運用前提**: MQTTは匿名許可（パスワード認証なし）
- **Grafana**: admin/パスワード認証
- **SQLite**: ファイル権限のみ（pi ユーザーが読み書き）
- **将来**: 外部公開する場合はMQTT認証 + TLS化を必ず追加

## 構築ステップ

1. ✅ 設計書作成
2. ⬜ Pi 4 に Raspberry Pi OS Lite (64-bit) インストール
3. ⬜ Pi 初期設定（SSH、git、基本パッケージ）
4. ⬜ リポジトリclone
5. ⬜ Mosquitto インストール・設定
6. ⬜ Python スクリプト + systemd サービス作成・起動
7. ⬜ Pico の `config.py` に Pi のIPアドレス設定 → MQTT送信テスト
8. ⬜ Grafana インストール・SQLite接続・ダッシュボード作成

**まずは 7 まで（PicoのデータがPiまで届く）を目標にする。**
Grafanaの可視化は後回しで、データ確認は SQLite の直接クエリで行う。

# サーバー設計書

最終更新: 2026-07-19

## 目的

PicoBox（区A/B/C 各台）から送られてくる温度データを収集・蓄積・可視化する。
農場に設置したモバイルルーター経由でクラウド（GCE）にMQTT送信し、自宅のRaspberry Piで可視化する。

**設計方針**: 手間を最小化する。Dockerやコンテナ抽象化は使わず、apt install と Python で完結させる。

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
        ┌──────────────────────────────┐
        │ カシムラ KD-249 モバイルルーター │  ← 農場設置
        │ (SORACOM plan-K2 SIM)        │
        └──────────────┬──���────────────┘
                       │ LTE
                       ▼
┌──────────────────────────────────────────────────┐
│  GCE (mqtt-broker / 34.58.138.105)               │
│  e2-micro (1GB RAM), us-central1-a               │
│                                                   │
│  ┌──────────────┐    ┌──────────────────┐        │
│  │ Mosquitto    │───>│ mqtt_logger.py   │        │
│  │ :1883       │    │ (バックアップ用)  │        │
│  │ (��証あり)   ��    └────────┬─────────┘        │
│  └──────────────┘             │                   │
│                               ▼                   │
│                    /var/lib/solar-heat/data.db     │
│                    (SQLite バックアップ)           │
└──────────────────────────────────────────────────┘
                       │
              MQTT subscribe (LAN→WAN)
                       │
┌──────────────────────────────────────────────────┐
│  Raspberry Pi 4（hp-server / 192.168.0.10）      │
│  Debian 13 (trixie) aarch64                      │
│  SD: 28GB / RAM: 3.7GB                           │
│                                                   │
│  ┌───────────���──────┐                            │
│  │ mqtt_logger.py   │  �� GCE Mosquittoを購読    │
│  │ (systemdサービス)│                            │
│  └────────┬─────────┘                            │
│           │                                       │
│           ▼                                       │
│  ┌────────────────────────┐                      │
│  │ /var/lib/solar-heat/   │                      │
│  │   data.db (SQLite)     │  ← 本番データ       │
│  └─────────��┬─────────────┘                      │
│             │                                     │
│             ▼                                     │
│  ┌────────────────────────┐                      │
│  │ Grafana :3000          │                      │
│  │ + frser-sqlite-datasource v4.0.2             │
│  └────────────────────────┘                      │
└──────────────────────────────────────────────────┘
```

## コンポーネント一覧

### GCE (mqtt-broker)

| 役割 | 採用 | バージョン | 備考 |
|---|---|---|---|
| MQTTブローカー | Mosquitto | 2.0.x | パスワード認証���picobox / solar-heat-2026） |
| MQTT購読・保存 | mqtt_logger.py | Python 3.x | バックアップ用 |
| データ保存 | SQLite | 3.x | /var/lib/solar-heat/data.db |

### Raspberry Pi (hp-server)

| 役割 | 採用 | バージョン | 備考 |
|---|---|---|---|
| MQTT購読・保存 | Python + paho-mqtt | Python 3.13.5 / paho-mqtt 2.1.0 | GCE Mosquittoを購読 |
| データ保存 | SQLite | 3.46.1 | /var/lib/solar-heat/data.db（本番） |
| 可視化 | Grafana + frser-sqlite-datasource | 13.0.1 / v4.0.2 | LAN内アクセスのみ |

## ネットワーク・ポート

| サービス | ホスト | ポート | 公開範囲 |
|---|---|---|---|
| Mosquitto | GCE (34.58.138.105) | 1883 | インターネット（認証必須） |
| Grafana | Pi (192.168.0.10) | 3000 | LAN内 |

### GCE ファイアウォールルール

| ルール名 | ポート | 用途 |
|---|---|---|
| allow-mqtt | tcp:1883 | PicoBox → Mosquitto |
| default-allow-ssh | tcp:22 | 管理用 |

## データフロ���

### Picoが送るMQTTメッセージ

30分間隔（INTERVAL_SEC = 1800）で発行：

| トピック | ペイロード（JSON） |
|---|---|
| `solar-heat/{zone}/{label}` | `{"time": "2021-01-01T...", "temp": 25.5}` |
| `solar-heat/{zone}/status` | `{"zone": "...", "bus_v": 5.06, "sd_status": "mount_failed", ...}` |
| `solar-heat/{zone}/power_alert` | `{"zone": "...", "bus_v": 4.0, "alert": "main_power_lost"}` |

> **注意**: `time` フィールドはPicoのRTC（NTP同期失敗で2021-01-01固定）。
> 正確な時刻は `received_at`（サーバー側付与UTC）を使用する。

### mqtt_logger のゾーン・ラベル変換

配線取り回しの都合でPicoBox筐体を入れ替えて設置したため、`mqtt_logger.py` で受信時にゾーン名を変換してDBに保存する。

```python
ZONE_REMAP = {"zone-a": "zone-c", "zone-c": "zone-a"}
```

| Picoが送信する zone | DBに保存される zone | 物理エリア |
|---|---|---|
| zone-a（Pico1） | **zone-c** | エリアC（微生物養生） |
| zone-b（Pico2） | zone-b | エリアB（標準養生） |
| zone-c（Pico3） | **zone-a** | エリアA（対照区） |

センサープローブも一部コネクタを差し替えている（詳細は `docs/sensor_registry.md` 参照）。
ラベル（S1〜S7）は常にGPIOピン＝物理配置深度を表すため、DB上のラベルは正確。

### SQLiteスキーマ

```sql
CREATE TABLE temperature (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,    -- Picoが送るISO8601（2021-01-01固定、参考値）
    received_at TEXT NOT NULL,    -- サーバー側の受信時刻（UTC、正確）
    zone        TEXT NOT NULL,
    label       TEXT NOT NULL,
    temp        REAL NOT NULL
);
CREATE INDEX idx_temp_zone_ts ON temperature(zone, timestamp);

CREATE TABLE device_status (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at TEXT NOT NULL,
    zone        TEXT NOT NULL,
    bus_v       REAL,
    sd_status   TEXT,
    wifi_attempts INTEGER,
    uptime_min  INTEGER
);

CREATE TABLE power_alert (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at TEXT NOT NULL,
    zone        TEXT NOT NULL,
    bus_v       REAL,
    alert       TEXT
);
```

## Grafana ダッシュボード

UID: `solar-heat-main`
URL: `http://192.168.0.10:3000/d/solar-heat-main/solar-heat-temperature-monitor`

| Panel ID | タイトル | 内容 |
|---|---|---|
| 1 | All Zones - Center 10cm | 全ゾーンのS1比較（3線） |
| 10 | Zone A (Control) | zone-a 全7センサー（7線） |
| 20 | Zone B (Standard) | zone-b 全7センサー（7線） |
| 30 | Zone C (Microbe) | zone-c 全7センサー（7線） |
| 40 | Depth - Center | 中央深度比較 A/B/C × 10/25/40cm（9線） |
| 41 | Depth - Edge | 辺縁深度比較 A/B/C × 10/25/40cm（9線） |
| 50 | Device Status | 最新デバイス状態テーブル |

### クエリ設計上の注意

- **frser-sqlite-datasource の `queryType: "time series"` はバグで使用不可**（v4.0.2, v4.0.6共に "can not convert to wide series" エラー）
- `queryType: "table"` を使用し、SQLでワイドフォーマット（PIVOT）に変換
- 時刻���ラムは `CAST(CAST(unixepoch(received_at)/60 AS INT)*60 AS REAL)*1000` （分丸めエポックms）
- `convertFieldType` トランスフォーメーションで `time` を時間型に変換
- `$__from / 1000` と `$__to / 1000` でGrafanaの時間範囲フィルタ��用
- Go バックエンドは `queryText` フィールドを読む（`rawQueryText` はフロントエンド用、両方記載）

## アクセス情報

| 項目 | 値 |
|---|---|
| **GCE** | |
| インスタンス名 | mqtt-broker |
| IP | 34.58.138.105 |
| SSH | `gcloud compute ssh nono@mqtt-broker --zone=us-central1-a` |
| MQTT認証 | user: `picobox` / pass: `solar-heat-2026` |
| **Raspberry Pi** | |
| ホスト名 | hp-server |
| IP | 192.168.0.10 |
| SSH | `ssh nono@192.168.0.10` |
| Grafana URL | http://192.168.0.10:3000 |
| Grafana ダッシュボードUID | `solar-heat-main` |
| Datasource UID | `P648C6F40D76405CF` |
| SQLite DB | `/var/lib/solar-heat/data.db` |

## よく使うコマンド

```bash
# === GCE ===
# MQTT受信確認
gcloud compute ssh nono@mqtt-broker --zone=us-central1-a --command="mosquitto_sub -h localhost -u picobox -P solar-heat-2026 -t 'solar-heat/#' -v"

# GCE mqtt_logger ログ
gcloud compute ssh nono@mqtt-broker --zone=us-central1-a --command="journalctl -u mqtt_logger -f"

# GCE バックアップDB確認
gcloud compute ssh nono@mqtt-broker --zone=us-central1-a --command="sqlite3 /var/lib/solar-heat/data.db 'SELECT zone, count(*), max(received_at) FROM temperature GROUP BY zone'"

# === Raspberry Pi ===
# mqtt_logger ログ
ssh nono@192.168.0.10 "journalctl -u mqtt_logger -f"

# DB確認
ssh nono@192.168.0.10 "sqlite3 /var/lib/solar-heat/data.db 'SELECT zone, count(*), max(received_at) FROM temperature GROUP BY zone'"

# ソフト更新
ssh nono@192.168.0.10 "cd ~/solar-heat && git pull && sudo systemctl restart mqtt_logger"

# Grafana ダッシュボード更新
ssh nono@192.168.0.10 "sudo cp ~/solar-heat/server/grafana/provisioning/dashboards/solar-heat.json /etc/grafana/provisioning/dashboards/ && sudo systemctl restart grafana-server"
```

## systemd サービス一覧

### GCE

| サービス | 状態 | 備考 |
|---|---|---|
| `mosquitto.service` | active/enabled | MQTTブローカー（認証あり） |
| `mqtt_logger.service` | active/enabled | バックアップ用データ収集 |

### Raspberry Pi

| サービス | 状態 | 備考 |
|---|---|---|
| `mqtt_logger.service` | active/enabled | GCE MQTTを購読 → SQLite保存 |
| `grafana-server.service` | active/enabled | 可視化（LAN内） |

## 既知の制約・課題

- **Pico RTC不正確**: NTP同期に失敗するため `timestamp` は常に 2021-01-01。`received_at` を正とする
- **SDカードマウント失敗**: 全PicoBoxで赤LED点滅（MCP1703ハンダ不良 or SDカード接触���良の可能性）
- **外部からのGrafana閲覧不可**: Pi は LAN内のみ。GitHub Pages (HTTPS) からの HTTP iframe は mixed content でブロックされる
- **GCE mosquitto.conf**: リポジトリ上の `server/mosquitto/mosquitto.conf` にはWebSocket (9001) の設定があるが、GCE���番では未適用（1883のみ）

## データベース現況（2026-07-19時点）

### Pi（本番）

| テーブル | zone-a (エリアA) | zone-b (エリアB) | zone-c (エリアC) |
|---|---|---|---|
| temperature | 153 | 197 | 1,968 |

### GCE（バックアップ）

| テーブル | zone-a | zone-b | zone-c |
|---|---|---|---|
| temperature | 133 | 168 | 119 |

> zone-c のレコード数が多いのは Pico1 の自宅ベンチテスト期間のデータを含むため。
> GCEは2026-07-12以降のデータのみ（MQTTブローカー移設日以降）。

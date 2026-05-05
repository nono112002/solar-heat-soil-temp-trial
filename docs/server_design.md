# サーバー設計書

最終更新: 2026-05-05

## 目的

PicoBox（区A/B/C 各台）から送られてくる温度データを **自宅内のRaspberry Pi 4** で受信・蓄積・可視化する。
クラウド（Ambient等）に依存せず、データ所有権を手元に保つ。

**設計方針**: 手間を最小化する。Dockerやコンテナ抽象化は使わず、apt install と Python で完結させる。

## 構築結果（2026-05-05）

End-to-End データ流通確認済み：

```
Pico W ──MQTT──> Mosquitto ──> mqtt_logger.py ──> SQLite ──> Grafana ──> ブラウザ
                                                                              ✅
```

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
│  Raspberry Pi 4（hp-server / 192.168.0.10）      │
│  Raspberry Pi OS Lite (64-bit) Debian 13         │
│                                                   │
│  ┌──────────┐    ┌──────────────────┐            │
│  │Mosquitto │───>│ mqtt_logger.py   │            │
│  │ :1883    │    │ (systemdサービス)│            │
│  └──────────┘    └────────┬─────────┘            │
│                           │                       │
│                           ▼                       │
│                  ┌────────────────────────┐      │
│                  │ /var/lib/solar-heat/   │      │
│                  │   data.db (SQLite)     │      │
│                  └──────────┬─────────────┘      │
│                             │                     │
│                             ▼                     │
│                  ┌────────────────────────┐      │
│                  │ Grafana :3000          │      │
│                  │ + SQLite plugin        │      │
│                  └────────────────────────┘      │
└──────────────────────────────────────────────────┘
                        │
                        ▼
                http://hp-server.local:3000
```

## コンポーネント実装内容

| 役割 | 採用 | インストール／配置 |
|---|---|---|
| MQTTブローカー | Mosquitto 2.0.21 | `apt install mosquitto mosquitto-clients` |
| MQTT購読・保存 | Python + paho-mqtt | `apt install python3-paho-mqtt` + `server/mqtt_logger.py` |
| データ保存 | SQLite 3.46 | Python標準ライブラリ + `apt install sqlite3` |
| 可視化 | Grafana 13.0 + frser-sqlite-datasource | Grafana公式aptリポジトリ + `grafana cli plugins install` |
| サービス管理 | systemd | OS標準 |

## ネットワーク・ポート

| サービス | ポート | 公開範囲 |
|---|---|---|
| Mosquitto | 1883 | LAN内 |
| Grafana | 3000 | LAN内（ブラウザ閲覧用） |

## データフロー詳細

### Picoが送るMQTTメッセージ

`pico/main.py` の `send_mqtt()` から30分ごとに発行：

| トピック | ペイロード（JSON） |
|---|---|
| `solar-heat/{zone}/{label}` | `{"time": "2026-...", "temp": 25.5}` |
| `solar-heat/{zone}/power_alert` | `{"zone": "...", "bus_v": 4.0, "alert": "main_power_lost"}` |

### SQLiteスキーマ

```sql
CREATE TABLE temperature (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,    -- Picoが送るISO8601
    received_at TEXT NOT NULL,    -- Pi側の受信時刻
    zone        TEXT NOT NULL,
    label       TEXT NOT NULL,
    temp        REAL NOT NULL
);
CREATE INDEX idx_temp_zone_ts ON temperature(zone, timestamp);

CREATE TABLE power_alert (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at TEXT NOT NULL,
    zone        TEXT NOT NULL,
    bus_v       REAL,
    alert       TEXT
);
```

## ディレクトリ構成（リポジトリ側）

```
server/
├── README.md                    # Pi側でのセットアップ手順
├── mqtt_logger.py               # MQTT購読 → SQLite保存
├── mqtt_logger.service          # systemdユニット定義
├── mosquitto/
│   └── mosquitto.conf           # MQTTブローカー設定
└── grafana/
    └── provisioning/
        └── datasources/
            └── sqlite.yml       # Grafanaデータソース自動登録
```

## Pi側の配置

| リポジトリ側 | Pi側配置 | 配置方法 |
|---|---|---|
| `server/mosquitto/mosquitto.conf` | `/etc/mosquitto/conf.d/solar-heat.conf` | シンボリックリンク |
| `server/mqtt_logger.service` | `/etc/systemd/system/mqtt_logger.service` | シンボリックリンク |
| `server/mqtt_logger.py` | `~/solar-heat/server/mqtt_logger.py` | git pullで自動反映 |
| `server/grafana/provisioning/datasources/sqlite.yml` | `/etc/grafana/provisioning/datasources/sqlite.yml` | **コピー（権限の都合）** |

> Grafana設定ファイルだけはGrafanaがhomeディレクトリ越しに読めない権限制約のため、シンボリックリンクではなくコピーで配置している。
> 設定変更時は `sudo cp ~/solar-heat/server/grafana/provisioning/datasources/sqlite.yml /etc/grafana/provisioning/datasources/ && sudo systemctl restart grafana-server` が必要。

## 開発・デプロイフロー

```
[開発機（Windows）]                [Raspberry Pi 4]
                                  
git push  ─────────────────────>  git pull
                                       │
                                       ▼
                                  sudo systemctl restart mqtt_logger
                                  (Grafana設定変更時のみ追加コピー)
                                       │
                                       ▼
                                  反映完了
```

## 実装上のハマりポイント（参考メモ）

1. **umqtt.simple モジュール不在**
   - MicroPython にデフォルトでは入っていない
   - 対処: `mpremote connect COM5 mip install umqtt.simple`

2. **config.py の ZONE 設定漏れ**
   - main.py が `config.ZONE` を参照するが定義されておらず初回はエラー
   - 対処: `ZONE = "zone-a"` を追加

3. **Grafana provisioning ファイルの権限**
   - シンボリックリンクの先がhomeディレクトリだとgrafanaユーザーが読めない
   - 対処: `chmod 755 /home/nono` + 設定ファイルは `root:grafana 640` でコピー配置

4. **SDマウント失敗時の起動停止**
   - main.py が SD マウント失敗で起動全体を止める
   - SD カード必須の運用なら現状OK、テスト用に分離するなら要検討

## アクセス情報

| 項目 | 値 |
|---|---|
| Pi ホスト名 | `hp-server.local` |
| Pi IPアドレス | `192.168.0.10` |
| SSH | `ssh nono@hp-server.local`（鍵認証） |
| Grafana URL | http://hp-server.local:3000 |
| Grafana初期ログイン | `admin` / `admin` |
| SQLite DB | `/var/lib/solar-heat/data.db` |
| ログ確認 | `journalctl -u mqtt_logger -f` |

## セキュリティ方針（現状）

- **LAN内運用前提**: MQTTは匿名許可
- **Grafana**: admin/パスワード認証
- **SSH**: 公開鍵認証（パスワードログインも残存）
- **将来**: 外部公開する場合はMQTT認証 + TLS化を必ず追加

## 残作業

- ⬜ Grafanaダッシュボード作成（複数ゾーン横並びの温度推移グラフ）
- ⬜ PicoBox 残り2台（区B、区C）の組み立て・設定
- ⬜ 各Picoの `config.py` でゾーン設定（zone-b, zone-c）
- ⬜ 屋外設置・防水対策
- ⬜ 長期運用テスト（電源断・WiFi切断時の挙動確認）

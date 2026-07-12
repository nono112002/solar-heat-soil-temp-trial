# サーバー設計書

最終更新: 2026-07-10

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
│  Debian 13 (trixie) aarch64                      │
│  SD: 28GB (24% 使用) / RAM: 3.7GB               │
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
│                  │ + frser-sqlite-datasource     │
│                  └────────────────────────┘      │
│                                                   │
│                  ┌────────────────────────┐      │
│                  │ Hugo :1313             │      │
│                  │ ポートフォリオHP        │      │
│                  └────────────────────────┘      │
└──────────────────────────────────────────────────┘
                        │
                ┌───────┴────────┐
                ▼                ▼
  http://192.168.0.10:3000   http://192.168.0.10:1313
      (Grafana)                (ポートフォリオ)
```

## コンポーネント実装内容

| 役割 | 採用 | バージョン | インストール／配置 |
|---|---|---|---|
| MQTTブローカー | Mosquitto | 2.0.21 | `apt install mosquitto mosquitto-clients` |
| MQTT購読・保存 | Python + paho-mqtt | Python 3.13.5 / paho-mqtt 2.1.0 | `apt install python3-paho-mqtt` + `server/mqtt_logger.py` |
| データ保存 | SQLite | 3.46.1 | Python標準ライブラリ + `apt install sqlite3` |
| 可視化 | Grafana + frser-sqlite-datasource | 13.0.1 | Grafana公式aptリポジトリ + `grafana cli plugins install` |
| ポートフォリオHP | Hugo + Blowfish テーマ | Hugo 0.131.0 / Blowfish v2.88.1 | `apt install hugo` + `git clone` |
| サービス管理 | systemd | OS標準 | — |

## ネットワーク・ポート

| サービス | ポート | 公開範囲 | 備考 |
|---|---|---|---|
| Mosquitto | 1883 | LAN内 | 匿名許可 |
| Grafana | 3000 | LAN内 | admin認証、匿名閲覧許可、iFrame埋め込み許可 |
| Hugo | 1313 | LAN内 | ポートフォリオHP（dashboard.html でGrafana iFrame 3分割表示） |

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
        ├── datasources/
        │   └── sqlite.yml       # Grafanaデータソース自動登録
        └── dashboards/
            ├── dashboards.yml   # ダッシュボードprovisioning設定
            └── solar-heat.json  # ダッシュボード定義（参考用）
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

## Pi側のディレクトリ構成

```
/home/nono/
├── solar-heat/              # git clone（データ収集系）
│   ├── server/
│   │   ├── mqtt_logger.py   # → systemd で常駐
│   │   └── mosquitto/
│   ├── pico/
│   ├── kicad/
│   └── docs/
└── portfolio/               # git clone（ポートフォリオHP）
    ├── config/
    ├── content/
    ├── layouts/
    ├── static/
    │   └── dashboard.html   # Grafana iFrame 3分割表示
    └── themes/
        └── blowfish/        # git submodule（v2.88.1固定）

/var/lib/solar-heat/
└── data.db                  # SQLiteデータベース（温度・ステータス・アラート）
```

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
| Pi ホスト名 | `hp-server` |
| Pi IPアドレス | `192.168.0.10` |
| SSH | `ssh nono@192.168.0.10` |
| Grafana URL | http://192.168.0.10:3000 |
| Grafana ダッシュボードUID | `9a4350e2-cfdf-4ed8-b916-bd06a9d448f6` |
| SQLite DB | `/var/lib/solar-heat/data.db` |
| ポートフォリオHP (LAN) | http://192.168.0.10:1313 |
| ポートフォリオHP (公開) | https://nono112002.github.io/ |
| HP リポジトリ | `nono112002/nono112002.github.io` |
| HP ローカルパス | `C:\Users\momon\work\portfolio\hugo` |

### よく使うコマンド

```bash
# ログ確認
journalctl -u mqtt_logger -f

# MQTT受信確認
mosquitto_sub -h localhost -t 'solar-heat/#' -v

# DB確認
sqlite3 /var/lib/solar-heat/data.db 'SELECT * FROM temperature ORDER BY id DESC LIMIT 10;'

# ソフト更新
cd ~/solar-heat && git pull && sudo systemctl restart mqtt_logger
cd ~/portfolio && git pull --recurse-submodules

# Hugo起動（systemd未登録、手動起動）
cd ~/portfolio && hugo server --bind 0.0.0.0 --baseURL http://192.168.0.10 -p 1313
```

## セキュリティ方針（現状）

- **LAN内運用前提**: MQTTは匿名許可
- **Grafana**: admin/パスワード認証
- **SSH**: 公開鍵認証（パスワードログインも残存）
- **将来**: 外部公開する場合はMQTT認証 + TLS化を必ず追加

## systemd サービス一覧

| サービス | 状態 | 自動起動 | 備考 |
|---|---|---|---|
| `mosquitto.service` | active | enabled | MQTTブローカー |
| `mqtt_logger.service` | active | enabled | MQTT→SQLite保存 |
| `grafana-server.service` | active | enabled | 可視化 |
| Hugo | active（手動起動） | **未登録** | `nohup hugo server ...` で起動中 |

> Hugo は systemd 未登録のため、Pi 再起動時に手動で起動する必要がある。
> 常駐化する場合は systemd ユニットファイルを作成すること。

## Grafana ダッシュボード構成

UID: `9a4350e2-cfdf-4ed8-b916-bd06a9d448f6`

| Panel ID | タイトル | 内容 |
|---|---|---|
| 1 | Zone-A | zone-a 全7センサー温度推移 |
| 2 | Zone-B | zone-b 全7センサー温度推移 |
| 3 | Zone-C | zone-c 全7センサー温度推移 |

ポートフォリオHP の `dashboard.html` からは上記3パネルを iFrame で埋め込み表示（上段2分割 + 下段フル幅）。

## データベース現況（2026-07-10時点）

| テーブル | レコード数 |
|---|---|
| temperature | 1,868 |
| device_status | 224 |
| power_alert | 1 |

DBファイルサイズ: 284KB

## 残作業

- ⬜ Hugo の systemd 常駐化
- ⬜ 屋外設置・防水対策
- ⬜ 長期運用テスト（電源断・WiFi切断時の挙動確認）
- ⬜ SIM（SORACOM plan-K2）導入後のモバイル通信テスト

# Solar-Heat サーバー（Raspberry Pi）

PicoBox から MQTT で送られる温度データを受信して SQLite に保存する。

詳細設計は [`docs/server_design.md`](../docs/server_design.md) を参照。

## 構成

| サービス | 役割 |
|---|---|
| Mosquitto (apt) | MQTT ブローカー |
| `mqtt_logger.py` (Python) | MQTT 購読 → SQLite 書き込み（systemd 常駐） |
| Grafana (apt) | 可視化（後で追加） |

## Pi セットアップ手順

### 1. 基本パッケージ

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git mosquitto mosquitto-clients python3-paho-mqtt
```

### 2. リポジトリ取得

```bash
cd ~
git clone https://github.com/nono112002/solar-heat-soil-temp-trial.git solar-heat
cd solar-heat
```

### 3. Mosquitto 設定（シンボリックリンク）

```bash
sudo ln -s ~/solar-heat/server/mosquitto/mosquitto.conf /etc/mosquitto/conf.d/solar-heat.conf
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

### 4. SQLite 保存先ディレクトリ作成

```bash
sudo mkdir -p /var/lib/solar-heat
sudo chown pi:pi /var/lib/solar-heat
```

### 5. mqtt_logger サービス起動

```bash
sudo ln -s ~/solar-heat/server/mqtt_logger.service /etc/systemd/system/mqtt_logger.service
sudo systemctl daemon-reload
sudo systemctl enable mqtt_logger
sudo systemctl start mqtt_logger
```

### 6. 動作確認

別ターミナルでMQTTを直接購読して、Picoが送信しているか確認：

```bash
mosquitto_sub -h localhost -t 'solar-heat/#' -v
```

ログ確認：

```bash
journalctl -u mqtt_logger -f
```

SQLite 中身確認：

```bash
sqlite3 /var/lib/solar-heat/data.db 'SELECT * FROM temperature ORDER BY id DESC LIMIT 10;'
```

## アップデート

開発機でコミット・プッシュ後、Pi 側で：

```bash
cd ~/solar-heat
git pull
sudo systemctl restart mqtt_logger
```

設定ファイルやスクリプトはシンボリックリンクなので、`git pull` で自動反映される。

## トラブルシューティング

| 症状 | 確認 |
|---|---|
| `mqtt_logger` が起動しない | `journalctl -u mqtt_logger -n 50` |
| MQTTメッセージが来ない | `mosquitto_sub -h localhost -t '#' -v` で全トピック監視 |
| Pico 側が接続できない | Pico の `config.py` の `MQTT_BROKER` が Pi の IP/ホスト名になっているか |
| ファイアウォール | `sudo ufw status`（Bookworm標準では無効のはず） |

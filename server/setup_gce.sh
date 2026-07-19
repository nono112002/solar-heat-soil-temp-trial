#!/bin/bash
# GCE セットアップスクリプト（Ubuntu/Debian想定）
# solar-heat サーバーを GCE に一元化する
#
# 使い方: ssh nono@34.58.138.105 で入って実行
#   chmod +x setup_gce.sh && sudo ./setup_gce.sh

set -euo pipefail

echo "=== 1. パッケージ更新 ==="
apt update && apt upgrade -y

echo "=== 2. Mosquitto (既に入っている想定だが念のため) ==="
apt install -y mosquitto mosquitto-clients

echo "=== 3. Python + paho-mqtt ==="
apt install -y python3 python3-paho-mqtt sqlite3

echo "=== 4. mqtt_logger セットアップ ==="
mkdir -p /var/lib/solar-heat
chown nono:nono /var/lib/solar-heat

# サービスファイルをコピー
cp /home/nono/solar-heat/server/mqtt_logger_gce.service /etc/systemd/system/mqtt_logger.service
systemctl daemon-reload
systemctl enable mqtt_logger
systemctl restart mqtt_logger

echo "=== 5. Grafana インストール ==="
apt install -y apt-transport-https software-properties-common wget
wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key
echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" \
  > /etc/apt/sources.list.d/grafana.list
apt update
apt install -y grafana

echo "=== 6. Grafana SQLite プラグイン ==="
grafana cli plugins install frser-sqlite-datasource

echo "=== 7. Grafana 設定（匿名閲覧 + iframe許可） ==="
cat >> /etc/grafana/grafana.ini << 'GRAFANA_CONF'

# --- Solar-Heat 追加設定 ---
[security]
allow_embedding = true

[auth.anonymous]
enabled = true
org_name = Main Org.
org_role = Viewer

[server]
root_url = http://34.58.138.105:3000
GRAFANA_CONF

echo "=== 8. Grafana provisioning ==="
mkdir -p /etc/grafana/provisioning/datasources
mkdir -p /etc/grafana/provisioning/dashboards
cp /home/nono/solar-heat/server/grafana/provisioning/datasources/sqlite.yml \
   /etc/grafana/provisioning/datasources/
cp /home/nono/solar-heat/server/grafana/provisioning/dashboards/dashboards.yml \
   /etc/grafana/provisioning/dashboards/
cp /home/nono/solar-heat/server/grafana/provisioning/dashboards/solar-heat.json \
   /etc/grafana/provisioning/dashboards/

systemctl enable grafana-server
systemctl restart grafana-server

echo "=== 9. Mosquitto WebSocket 追加 ==="
cp /home/nono/solar-heat/server/mosquitto/mosquitto.conf /etc/mosquitto/conf.d/solar-heat.conf
systemctl restart mosquitto

echo "=== 完了 ==="
echo "Grafana: http://34.58.138.105:3000"
echo "MQTT:    34.58.138.105:1883"
echo "MQTT WS: 34.58.138.105:9001"
echo ""
echo "GCE ファイアウォールで tcp:3000,9001 を開放してください:"
echo "  gcloud compute firewall-rules create allow-grafana --allow tcp:3000,tcp:9001 --target-tags=solar-heat"

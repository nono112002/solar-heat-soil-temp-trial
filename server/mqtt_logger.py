"""
MQTT メッセージを購読してSQLiteに保存するロガー

Pico W から `solar-heat/{zone}/{label}` および
`solar-heat/{zone}/power_alert` トピックに送信されたメッセージを受信し、
SQLiteのテーブルに記録する。

systemd サービスとして常駐起動する想定。
"""
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

# --- 設定（環境変数で上書き可能） ---
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = "solar-heat/+/+"
DB_PATH = Path(os.environ.get("DB_PATH", "/var/lib/solar-heat/data.db"))

# --- ログ ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("mqtt_logger")


# --- SQLite ---
def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS temperature (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            received_at TEXT NOT NULL,
            zone        TEXT NOT NULL,
            label       TEXT NOT NULL,
            temp        REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_temp_zone_ts ON temperature(zone, timestamp);

        CREATE TABLE IF NOT EXISTS power_alert (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at TEXT NOT NULL,
            zone        TEXT NOT NULL,
            bus_v       REAL,
            alert       TEXT
        );

        CREATE TABLE IF NOT EXISTS device_status (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at   TEXT NOT NULL,
            zone          TEXT NOT NULL,
            bus_v         REAL,
            sd_status     TEXT,
            wifi_attempts INTEGER,
            uptime_min    INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_status_zone_ts ON device_status(zone, received_at);
        """
    )
    conn.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- MQTT コールバック ---
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log.info("Connected to MQTT broker at %s:%d", MQTT_HOST, MQTT_PORT)
        client.subscribe(MQTT_TOPIC)
        log.info("Subscribed to %s", MQTT_TOPIC)
    else:
        log.error("MQTT connect failed: rc=%s", rc)


def on_message(client, userdata, msg):
    conn: sqlite3.Connection = userdata["conn"]
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        log.warning("Invalid JSON on %s: %s", topic, e)
        return

    parts = topic.split("/")
    if len(parts) != 3 or parts[0] != "solar-heat":
        log.warning("Unexpected topic: %s", topic)
        return
    _, zone, leaf = parts
    received_at = now_iso()

    try:
        if leaf == "power_alert":
            conn.execute(
                "INSERT INTO power_alert (received_at, zone, bus_v, alert) VALUES (?, ?, ?, ?)",
                (received_at, zone, payload.get("bus_v"), payload.get("alert")),
            )
            log.info("[ALERT] zone=%s bus_v=%s", zone, payload.get("bus_v"))
        elif leaf == "status":
            conn.execute(
                "INSERT INTO device_status (received_at, zone, bus_v, sd_status, wifi_attempts, uptime_min) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    received_at,
                    zone,
                    payload.get("bus_v"),
                    payload.get("sd_status"),
                    payload.get("wifi_attempts"),
                    payload.get("uptime_min"),
                ),
            )
            log.info("[STATUS] zone=%s sd=%s wifi_att=%s uptime=%smin",
                     zone, payload.get("sd_status"), payload.get("wifi_attempts"),
                     payload.get("uptime_min"))
        else:
            conn.execute(
                "INSERT INTO temperature (timestamp, received_at, zone, label, temp) VALUES (?, ?, ?, ?, ?)",
                (
                    payload.get("time", received_at),
                    received_at,
                    zone,
                    leaf,
                    float(payload["temp"]),
                ),
            )
            log.info("zone=%s label=%s temp=%.2f", zone, leaf, payload["temp"])
        conn.commit()
    except Exception as e:
        log.exception("DB insert failed: %s", e)


# --- メイン ---
def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        userdata={"conn": conn},
    )
    client.on_connect = on_connect
    client.on_message = on_message

    log.info("Starting MQTT logger (DB: %s)", DB_PATH)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        log.info("Interrupted, shutting down")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

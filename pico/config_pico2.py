# config.py — Pico2（エリアB設置）
# GP8(S1)とGP10(S3)のプローブが入れ替わっている → 10cm⇔40cm

WIFI_SSID     = "***REDACTED_SSID***"
WIFI_PASSWORD = "***REDACTED***"

AMBIENT_CHANNEL_ID = 99639
AMBIENT_WRITE_KEY  = "***REDACTED***"

MQTT_BROKER = "34.58.138.105"
MQTT_PORT   = 1883
MQTT_USER   = "picobox"
MQTT_PASS   = "***REDACTED***"

ZONE = "zone-b"

SENSOR_PINS = {
    8:  "S3_center_40cm",
    9:  "S2_center_25cm",
    10: "S1_center_10cm",
    11: "S4_edge_10cm",
    12: "S5_edge_25cm",
    13: "S6_edge_40cm",
    14: "S7_outdoor",
}

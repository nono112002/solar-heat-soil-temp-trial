# config.py — Pico2（エリアB設置）
# GP8(S1)とGP10(S3)のプローブが入れ替わっている → 15cm⇔40cm
# GP14は外気温から土壌5cm（BLOF公式の基準深さ・参考値）に差し替え（2026-07-28 08:50）

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
    10: "S1_center_15cm",
    11: "S4_edge_15cm",
    12: "S5_edge_25cm",
    13: "S6_edge_40cm",
    14: "S7_soil_5cm",
}

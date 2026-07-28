# config.py — Pico3（エリアA設置）
# 筐体はPico3だが、物理的にはエリアAに設置されている
# GP8⇔GP10(中央15cm⇔40cm)、GP12⇔GP13(端部25cm⇔40cm) が入れ替わっている
# GP14は外気温から土壌5cm（BLOF公式の基準深さ・参考値）に差し替え（2026-07-28 08:50）

WIFI_SSID     = "***REDACTED_SSID***"
WIFI_PASSWORD = "***REDACTED***"

AMBIENT_CHANNEL_ID = 99639
AMBIENT_WRITE_KEY  = "***REDACTED***"

MQTT_BROKER = "34.58.138.105"
MQTT_PORT   = 1883
MQTT_USER   = "picobox"
MQTT_PASS   = "***REDACTED***"

ZONE = "zone-a"

SENSOR_PINS = {
    8:  "S3_center_40cm",
    9:  "S2_center_25cm",
    10: "S1_center_15cm",
    11: "S4_edge_15cm",
    12: "S6_edge_40cm",
    13: "S5_edge_25cm",
    14: "S7_soil_5cm",
}

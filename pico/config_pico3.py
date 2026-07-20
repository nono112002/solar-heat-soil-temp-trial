# config.py — Pico3（エリアA設置）
# 筐体はPico3だが、物理的にはエリアAに設置されている
# GP8⇔GP10(中央10cm⇔40cm)、GP12⇔GP13(端部25cm⇔40cm) が入れ替わっている

WIFI_SSID     = "field_wifi"
WIFI_PASSWORD = "nono-field"

AMBIENT_CHANNEL_ID = 99639
AMBIENT_WRITE_KEY  = "03c50d0513f9b3ee"

MQTT_BROKER = "34.58.138.105"
MQTT_PORT   = 1883
MQTT_USER   = "picobox"
MQTT_PASS   = "solar-heat-2026"

ZONE = "zone-a"

SENSOR_PINS = {
    8:  "S3_center_40cm",
    9:  "S2_center_25cm",
    10: "S1_center_10cm",
    11: "S4_edge_10cm",
    12: "S6_edge_40cm",
    13: "S5_edge_25cm",
    14: "S7_outdoor",
}

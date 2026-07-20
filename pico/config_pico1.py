# config.py — Pico1（エリアC設置）
# 筐体はPico1だが、物理的にはエリアCに設置されている
# センサーピン配置はデフォルトのまま（リマップ不要）

WIFI_SSID     = "field_wifi"
WIFI_PASSWORD = "nono-field"

AMBIENT_CHANNEL_ID = 99639
AMBIENT_WRITE_KEY  = "03c50d0513f9b3ee"

MQTT_BROKER = "34.58.138.105"
MQTT_PORT   = 1883
MQTT_USER   = "picobox"
MQTT_PASS   = "solar-heat-2026"

ZONE = "zone-c"

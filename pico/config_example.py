# config_example.py
# このファイルをコピーして config_pico1.py 等にリネームし、実際の値を入力してください
# config_pico*.py は .gitignore により Git 管理対象外です
#
# センサーIDのマッピングは SD カードの sensor_map.json で管理します
# sensor_map_template.json を参考に作成してください

# WiFi
WIFI_SSID     = "your_ssid"
WIFI_PASSWORD = "your_password"

# Ambient
AMBIENT_CHANNEL_ID = 0               # チャンネルID（数値）
AMBIENT_WRITE_KEY  = "your_write_key"

# MQTT
MQTT_BROKER = "your_mqtt_host"       # GCEまたはラズパイのIP
MQTT_PORT   = 1883
MQTT_USER   = "your_user"
MQTT_PASS   = "your_pass"

# ゾーン識別（区A/B/C）
ZONE = "zone-a"                      # zone-a / zone-b / zone-c

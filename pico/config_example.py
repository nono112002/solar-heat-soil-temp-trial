# config_example.py
# このファイルをコピーして config.py にリネームし、実際の値を入力してください
# config.py は .gitignore により Git 管理対象外です
#
# センサーIDのマッピングは SD カードの sensor_map.json で管理します
# sensor_map_template.json を参考に作成してください

# WiFi
WIFI_SSID     = "your_ssid"
WIFI_PASSWORD = "your_password"

# Ambient
AMBIENT_CHANNEL_ID = 0           # チャンネルID（数値）
AMBIENT_WRITE_KEY  = "your_write_key"

# MQTT（Raspberry Pi サーバー）
MQTT_BROKER = "192.168.x.x"      # ラズパイのIPアドレス
MQTT_PORT   = 1883

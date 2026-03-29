# config_example.py
# このファイルをコピーして config.py にリネームし、実際の値を入力してください
# config.py は .gitignore により Git 管理対象外です

# WiFi
WIFI_SSID = "your_ssid"
WIFI_PASSWORD = "your_password"

# Ambient
AMBIENT_CHANNEL_ID = 0       # チャンネルID（数値）
AMBIENT_WRITE_KEY  = "your_write_key"

# MQTT（自宅ラズパイ）
MQTT_BROKER = "192.168.x.x"  # ラズパイのIPアドレス
MQTT_PORT   = 1883

# このPicoが担当する区（zone-a / zone-b / zone-c）
ZONE = "zone-a"

# DS18B20 センサーID（scan_ids.py を実行して取得してください）
# 中央地点（GP21バス）
ID_CENTER_10 = "28xxxxxx"    # 深度10cm
ID_CENTER_25 = "28yyyyyy"    # 深度25cm
ID_CENTER_40 = "28zzzzzz"    # 深度40cm
# エッジ地点（GP22バス）
ID_EDGE_10   = "28aaaaaa"    # 深度10cm
ID_EDGE_25   = "28bbbbbb"    # 深度25cm
ID_EDGE_40   = "28cccccc"    # 深度40cm

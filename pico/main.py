"""
Raspberry Pi Pico W - 太陽熱養生 温度ロガー
機能: DS18B20 複数センサ / SDカード記録 / Ambient送信 / MQTT送信
"""
import machine
import onewire
import ds18x20
import time
import sdcard
import os
import network
import ntptime
import ujson
import config

try:
    from umqtt.simple import MQTTClient
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

# --- ピン定義 ---
PIN_SD_SCK  = 18
PIN_SD_MOSI = 19
PIN_SD_MISO = 16
PIN_SD_CS   = 17
PIN_BUS1    = 21   # 中央地点センサーバス
PIN_BUS2    = 22   # エッジ地点センサーバス
PIN_LED_TX  = 15   # データ送信時 LED

# --- センサーIDとラベルのマッピング ---
SENSOR_MAP = {
    config.ID_CENTER_10: "center_10cm",
    config.ID_CENTER_25: "center_25cm",
    config.ID_CENTER_40: "center_40cm",
    config.ID_EDGE_10:   "edge_10cm",
    config.ID_EDGE_25:   "edge_25cm",
    config.ID_EDGE_40:   "edge_40cm",
}

INTERVAL_SEC = 600  # 計測間隔（10分）

led_tx = machine.Pin(PIN_LED_TX, machine.Pin.OUT)


# --- WiFi ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return True
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            return True
        time.sleep(1)
    return False


# --- NTP ---
def sync_ntp():
    try:
        ntptime.settime()
    except Exception as e:
        print("NTP error:", e)


# --- SDカード ---
def mount_sd():
    spi = machine.SPI(0,
        sck=machine.Pin(PIN_SD_SCK),
        mosi=machine.Pin(PIN_SD_MOSI),
        miso=machine.Pin(PIN_SD_MISO))
    sd = sdcard.SDCard(spi, machine.Pin(PIN_SD_CS))
    os.mount(os.VfsFat(sd), "/sd")


def log_to_sd(ts, data):
    """CSVにタイムスタンプ付きで記録"""
    fname = "/sd/{}_log_{:04d}{:02d}{:02d}.csv".format(config.ZONE, ts[0], ts[1], ts[2])
    need_header = not _exists(fname)
    with open(fname, "a") as f:
        if need_header:
            f.write("datetime,label,temp_c\n")
        dt = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*ts[:6])
        for label, temp in data.items():
            f.write("{},{},{:.2f}\n".format(dt, label, temp))


def _exists(path):
    try:
        os.stat(path)
        return True
    except:
        return False


# --- センサー読み取り ---
def read_sensors():
    results = {}
    for pin_num in [PIN_BUS1, PIN_BUS2]:
        ow  = onewire.OneWire(machine.Pin(pin_num))
        ds  = ds18x20.DS18X20(ow)
        roms = ds.scan()
        if not roms:
            continue
        ds.convert_temp()
        time.sleep_ms(750)
        for rom in roms:
            id_str = ''.join(['{:02x}'.format(b) for b in rom])
            label  = SENSOR_MAP.get(id_str, "unknown_" + id_str[:8])
            results[label] = ds.read_temp(rom)
    return results


# --- Ambient ---
def send_ambient(data):
    try:
        import urequests
        keys    = sorted(data.keys())
        payload = {"writeKey": config.AMBIENT_WRITE_KEY}
        for i, key in enumerate(keys[:8]):
            payload["d{}".format(i + 1)] = round(data[key], 2)
        url = "http://ambidata.io/api/v2/channels/{}/data".format(config.AMBIENT_CHANNEL_ID)
        res = urequests.post(url,
                             headers={"Content-Type": "application/json"},
                             data=ujson.dumps(payload))
        res.close()
        return True
    except Exception as e:
        print("Ambient error:", e)
        return False


# --- MQTT ---
def send_mqtt(ts, data):
    if not MQTT_AVAILABLE:
        return False
    try:
        client = MQTTClient(
            "pico_{}".format(config.ZONE),
            config.MQTT_BROKER,
            port=config.MQTT_PORT)
        client.connect()
        dt = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*ts[:6])
        for label, temp in data.items():
            topic   = "farm/solar-heat/{}/{}".format(config.ZONE, label)
            payload = ujson.dumps({"time": dt, "temp": round(temp, 2)})
            client.publish(topic, payload)
        client.disconnect()
        return True
    except Exception as e:
        print("MQTT error:", e)
        return False


# --- LED ---
def blink(n=2):
    for _ in range(n):
        led_tx.on()
        time.sleep_ms(150)
        led_tx.off()
        time.sleep_ms(150)


# --- 起動 ---
mount_sd()
if connect_wifi():
    sync_ntp()

# --- メインループ ---
while True:
    ts   = time.localtime()
    data = read_sensors()
    print(ts[:6], data)

    log_to_sd(ts, data)

    if connect_wifi():
        ok_mqtt    = send_mqtt(ts, data)
        ok_ambient = send_ambient(data)
        if ok_mqtt or ok_ambient:
            blink(2)
    else:
        print("WiFi unavailable - SD only")

    time.sleep(INTERVAL_SEC)

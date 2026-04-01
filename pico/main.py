"""
Raspberry Pi Pico W - 太陽熱養生 温度ロガー
機能: DS18B20 複数センサ / SDカード記録 / Ambient送信 / MQTT送信

センサーマッピングは SD カードの sensor_map.json で管理
  {"zone": "zone-a", "sensors": {"<ID>": "<label>", ...}}
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
PIN_SD_SCK    = 2
PIN_SD_MOSI   = 3
PIN_SD_MISO   = 4
PIN_SD_CS     = 5
PIN_SD_DETECT = 6    # カード検出（挿入時 LOW）
PIN_BUS       = 7    # 1-Wire バス（全センサー共通）
PIN_LED_TX    = 15   # データ送信時 LED

INTERVAL_SEC = 30    # 計測間隔（秒）※デバッグ用 / 本番は1800
TIME_OFFSET  = 9 * 3600  # JST (UTC+9)

led_tx    = machine.Pin(PIN_LED_TX, machine.Pin.OUT)
sd_detect = machine.Pin(PIN_SD_DETECT, machine.Pin.IN, machine.Pin.PULL_UP)


# --- SDカード ---
def is_sd_inserted():
    return sd_detect.value() == 0  # LOW = 挿入済み


def mount_sd():
    if not is_sd_inserted():
        raise OSError("SD card not inserted (card detect = HIGH)")
    try:
        spi = machine.SPI(0,
            sck=machine.Pin(PIN_SD_SCK),
            mosi=machine.Pin(PIN_SD_MOSI),
            miso=machine.Pin(PIN_SD_MISO))
        sd = sdcard.SDCard(spi, machine.Pin(PIN_SD_CS))
        os.mount(os.VfsFat(sd), "/sd")
    except OSError as e:
        raise OSError("SD mount failed (contact error?): {}".format(e))


def load_sensor_map():
    """SDカードの sensor_map.json からゾーンとIDマッピングを読み込む"""
    try:
        with open("/sd/sensor_map.json", "r") as f:
            data = ujson.load(f)
        zone       = data.get("zone", "unknown")
        sensor_map = data.get("sensors", {})
        print("sensor_map loaded: zone={} / {} sensors".format(zone, len(sensor_map)))
        return zone, sensor_map
    except Exception as e:
        print("sensor_map.json load error:", e)
        return "unknown", {}


def _exists(path):
    try:
        os.stat(path)
        return True
    except:
        return False


def log_to_sd(ts, zone, data, sensor_map):
    fname = "/sd/{}_log_{:04d}{:02d}{:02d}.csv".format(zone, ts[0], ts[1], ts[2])
    labels = sorted(sensor_map.values())  # 列順を常に固定
    need_header = not _exists(fname)
    try:
        with open(fname, "a") as f:
            if need_header:
                f.write("datetime," + ",".join(labels) + "\n")
            dt = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*ts[:6])
            row = [dt] + ["{:.2f}".format(data[l]) if l in data else "" for l in labels]
            f.write(",".join(row) + "\n")
        print("[SD] OK -> {}".format(fname))
    except Exception as e:
        print("[SD] ERROR:", e)


# --- WiFi ---
def wifi_off():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("[WiFi] already connected")
        return True
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            print("[WiFi] connected:", wlan.ifconfig()[0])
            return True
        time.sleep(1)
    print("[WiFi] ERROR: connect timeout")
    return False


# --- NTP ---
def sync_ntp():
    try:
        ntptime.settime()
        print("NTP synced (UTC)")
    except Exception as e:
        print("NTP error:", e)


def jst_time():
    """UTC → JST (UTC+9) に変換して返す"""
    return time.localtime(time.time() + TIME_OFFSET)


# --- センサー読み取り ---
def read_sensors(sensor_map):
    results = {}
    ow   = onewire.OneWire(machine.Pin(PIN_BUS))
    ds   = ds18x20.DS18X20(ow)
    roms = ds.scan()
    if not roms:
        print("No sensors found")
        return results
    ds.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        id_str = ''.join(['{:02x}'.format(b) for b in rom])
        label  = sensor_map.get(id_str, "unknown_" + id_str[:8])
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
        print("[Ambient] OK status={}".format(res.status_code))
        res.close()
        return True
    except Exception as e:
        print("[Ambient] ERROR:", e)
        return False


# --- MQTT ---
def send_mqtt(ts, zone, data):
    if not MQTT_AVAILABLE:
        return False
    try:
        client = MQTTClient("pico_{}".format(zone), config.MQTT_BROKER, port=config.MQTT_PORT)
        client.connect()
        dt = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*ts[:6])
        for label, temp in data.items():
            topic   = "solar-heat/{}/{}".format(zone, label)
            payload = ujson.dumps({"time": dt, "temp": round(temp, 2)})
            client.publish(topic, payload)
        client.disconnect()
        print("[MQTT] OK -> {} topics".format(len(data)))
        return True
    except Exception as e:
        print("[MQTT] ERROR:", e)
        return False


# --- LED ---
def blink(n=2):
    for _ in range(n):
        led_tx.on()
        time.sleep_ms(150)
        led_tx.off()
        time.sleep_ms(150)


# --- 起動 ---
wifi_off()  # SDマウント前にWiFiを切る

try:
    mount_sd()
    print("SD mounted OK")
except OSError as e:
    print("ERROR:", e)
    raise  # 起動停止

zone, sensor_map = load_sensor_map()

# 初回のみNTP同期
if connect_wifi():
    sync_ntp()
    wifi_off()

# --- メインループ ---
while True:
    ts   = jst_time()
    data = read_sensors(sensor_map)
    print(ts[:6], data)

    log_to_sd(ts, zone, data, sensor_map)

    # WiFi ON → 送信 → WiFi OFF
    if connect_wifi():
        ok_mqtt    = send_mqtt(ts, zone, data)
        ok_ambient = send_ambient(data)
        wifi_off()
        if ok_mqtt or ok_ambient:
            blink(2)
    else:
        print("WiFi unavailable - SD only")
        wifi_off()

    time.sleep(INTERVAL_SEC)

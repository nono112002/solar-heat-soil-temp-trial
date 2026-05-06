"""
Raspberry Pi Pico W - 太陽熱養生 温度ロガー
機能: DS18B20 個別GPIO / SDカード記録 / Ambient送信 / MQTT送信 / ヘルス監視

各センサーは専用GPIOピンに直結（1-Wire バス方式廃止）
ゾーン名は config.py の ZONE 変数で管理

赤LED 表示パターン:
  消灯       正常
  常時点灯   電源異常（bus_v < 4.0V）
  低速点滅   SD異常（マウント失敗・書き込み失敗・カード未挿入）
  高速点滅   電源異常 + SD異常 同時発生
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
PIN_LED_TX    = 15   # 送信／ステータスLED
PIN_POWER_MON = 26   # 主電源監視 ADC（10kΩ/10kΩ分圧）

# 5V入力時: GP26 = 2.5V。閾値4.0V入力 → GP26 = 2.0V
POWER_THRESHOLD_V = 4.0

# DS18B20 個別GPIO
SENSOR_PINS = {
    8:  "S1_center_10cm",
    9:  "S2_center_25cm",
    10: "S3_center_40cm",
    11: "S4_edge_10cm",
    12: "S5_edge_25cm",
    13: "S6_edge_40cm",
    14: "S7_outdoor",
}

INTERVAL_SEC = 1800  # 計測間隔（秒）= 30分
TIME_OFFSET  = 9 * 3600  # JST (UTC+9)

led_tx    = machine.Pin(PIN_LED_TX, machine.Pin.OUT)
sd_detect = machine.Pin(PIN_SD_DETECT, machine.Pin.IN, machine.Pin.PULL_UP)
adc_power = machine.ADC(PIN_POWER_MON)

# --- グローバル状態 ---
sd_status = "unknown"           # "ok" / "no_card" / "mount_failed" / "write_failed" / "ok_after_remount"
sd_mounted = False
last_wifi_attempts = 0
boot_time = None  # NTP同期後に設定（同期前はNoneのまま）


# --- LED ステートマシン（Timer駆動で連続点滅） ---
LED_OFF        = 0
LED_SOLID      = 1   # 電源異常
LED_SLOW_BLINK = 2   # SD異常（1Hz）
LED_FAST_BLINK = 3   # 両方同時（5Hz）

_led_state = LED_OFF
_led_counter = 0

# センサー状態: {label: True(正常) / False(未検出・読み取りエラー)}
sensor_status = {}


def _led_tick(t):
    global _led_counter
    if _led_state == LED_OFF:
        return  # Timerは触らない（手動blink可）
    if _led_state == LED_SOLID:
        led_tx.on()
        return
    _led_counter = (_led_counter + 1) % 10
    if _led_state == LED_SLOW_BLINK:
        led_tx.value(1 if _led_counter < 5 else 0)
    elif _led_state == LED_FAST_BLINK:
        led_tx.value(_led_counter % 2)


_led_timer = machine.Timer()
_led_timer.init(period=100, mode=machine.Timer.PERIODIC, callback=_led_tick)


def set_led_state(power_alert, sd_alert):
    """電源・SDのアラート状態からLED状態を決定"""
    global _led_state, _led_counter
    if power_alert and sd_alert:
        new_state = LED_FAST_BLINK
    elif power_alert:
        new_state = LED_SOLID
    elif sd_alert:
        new_state = LED_SLOW_BLINK
    else:
        new_state = LED_OFF
    if new_state != _led_state:
        _led_state = new_state
        _led_counter = 0
        if new_state == LED_OFF:
            led_tx.off()


def blink_tx(n=2):
    """送信成功のブリンク。アラート中はスキップ"""
    if _led_state != LED_OFF:
        return
    for _ in range(n):
        led_tx.on()
        time.sleep_ms(150)
        led_tx.off()
        time.sleep_ms(150)


# --- SDカード ---
def is_sd_inserted():
    return sd_detect.value() == 0  # LOW = 挿入済み


def mount_sd():
    """SDをマウント。成功でTrue、失敗でFalse（例外を投げない）"""
    global sd_mounted, sd_status
    if not is_sd_inserted():
        sd_status = "no_card"
        sd_mounted = False
        return False
    try:
        spi = machine.SPI(0,
            sck=machine.Pin(PIN_SD_SCK),
            mosi=machine.Pin(PIN_SD_MOSI),
            miso=machine.Pin(PIN_SD_MISO))
        sd = sdcard.SDCard(spi, machine.Pin(PIN_SD_CS))
        os.mount(os.VfsFat(sd), "/sd")
        sd_mounted = True
        sd_status = "ok"
        return True
    except Exception as e:
        print("[SD] mount failed:", e)
        sd_status = "mount_failed"
        sd_mounted = False
        return False


def umount_sd():
    global sd_mounted
    try:
        os.umount("/sd")
    except Exception:
        pass
    sd_mounted = False


def _exists(path):
    try:
        os.stat(path)
        return True
    except:
        return False


def _write_csv(ts, data):
    zone   = config.ZONE
    fname  = "/sd/{}_log_{:04d}{:02d}{:02d}.csv".format(zone, ts[0], ts[1], ts[2])
    labels = [SENSOR_PINS[p] for p in sorted(SENSOR_PINS)]
    need_header = not _exists(fname)
    with open(fname, "a") as f:
        if need_header:
            f.write("datetime," + ",".join(labels) + "\n")
        dt  = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*ts[:6])
        row = [dt] + ["{:.2f}".format(data[l]) if l in data else "" for l in labels]
        f.write(",".join(row) + "\n")
    return fname


def log_to_sd_with_recovery(ts, data):
    """書き込み失敗時に再マウント試行。状態を sd_status に反映"""
    global sd_status, sd_mounted

    # 1. カード検出チェック
    if not is_sd_inserted():
        sd_status = "no_card"
        sd_mounted = False
        print("[SD] no card detected")
        return False

    # 2. マウントされていなければマウント試行
    if not sd_mounted:
        if not mount_sd():
            return False

    # 3. 書き込み試行
    try:
        fname = _write_csv(ts, data)
        sd_status = "ok"
        print("[SD] OK -> {}".format(fname))
        return True
    except Exception as e:
        print("[SD] write failed:", e)
        # 4. 再マウントしてもう一度
        umount_sd()
        if mount_sd():
            try:
                fname = _write_csv(ts, data)
                sd_status = "ok_after_remount"
                print("[SD] OK after remount -> {}".format(fname))
                return True
            except Exception as e2:
                print("[SD] write failed after remount:", e2)
                sd_status = "write_failed"
                sd_mounted = False
                return False
        sd_status = "write_failed"
        return False


# --- WiFi ---
def wifi_off():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)


def connect_wifi():
    """WiFiを一度OFFしてから接続。失敗時は1回リトライ（最大2回試行）"""
    global last_wifi_attempts
    for attempt in range(1, 3):
        last_wifi_attempts = attempt
        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)
        time.sleep_ms(500)
        wlan.active(True)
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                print("[WiFi] connected (attempt {}):".format(attempt), wlan.ifconfig()[0])
                return True
            time.sleep(1)
        print("[WiFi] attempt {} timeout".format(attempt))
    print("[WiFi] ERROR: all attempts failed")
    return False


# --- NTP ---
def sync_ntp():
    global boot_time
    try:
        ntptime.settime()
        boot_time = time.time()  # NTP同期後に記録（uptime計算の基点）
        print("NTP synced (UTC)")
    except Exception as e:
        print("NTP error:", e)


def jst_time():
    return time.localtime(time.time() + TIME_OFFSET)


# --- センサー読み取り ---
def read_sensors():
    """全センサーを一括読み取り。sensor_status を毎サイクル更新する。
    True=正常, False=未検出またはエラー"""
    global sensor_status

    instances = {}
    for pin_num, label in SENSOR_PINS.items():
        try:
            ow   = onewire.OneWire(machine.Pin(pin_num))
            ds   = ds18x20.DS18X20(ow)
            roms = ds.scan()
            if not roms:
                print("[SENSOR] GP{} no sensor".format(pin_num))
                sensor_status[label] = False
                continue
            ds.convert_temp()
            instances[pin_num] = (ds, roms[0], label)
        except Exception as e:
            print("[SENSOR] GP{} scan error: {}".format(pin_num, e))
            sensor_status[label] = False

    time.sleep_ms(750)  # 全センサー変換完了待ち（1回のみ）

    results = {}
    for pin_num, (ds, rom, label) in instances.items():
        try:
            results[label] = ds.read_temp(rom)
            sensor_status[label] = True
        except Exception as e:
            print("[SENSOR] GP{} read error: {}".format(pin_num, e))
            sensor_status[label] = False
    return results


# --- Ambient ---
def send_ambient(data):
    try:
        import urequests
        labels  = [SENSOR_PINS[p] for p in sorted(SENSOR_PINS)]
        payload = {"writeKey": config.AMBIENT_WRITE_KEY}
        for i, label in enumerate(labels[:8]):
            if label in data:
                payload["d{}".format(i + 1)] = round(data[label], 2)
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
def send_mqtt(ts, data):
    if not MQTT_AVAILABLE:
        return False
    try:
        zone   = config.ZONE
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


def send_status(ts, bus_v):
    """デバイス自身のヘルス状態を送る。
    トピック: solar-heat/{zone}/status
    含む情報: SD状態, センサー正常/異常ラベル, 電源電圧, WiFi試行回数, 起動からの経過時間"""
    if not MQTT_AVAILABLE:
        return
    try:
        zone = config.ZONE
        client = MQTTClient("pico_{}_status".format(zone), config.MQTT_BROKER, port=config.MQTT_PORT)
        client.connect()
        dt = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*ts[:6])
        uptime_min = (time.time() - boot_time) // 60 if boot_time else -1
        ng_sensors = [l for l, ok in sensor_status.items() if not ok]
        payload = ujson.dumps({
            "time":         dt,
            "zone":         zone,
            "bus_v":        round(bus_v, 2),
            "sd_status":    sd_status,
            "sensors_ok":   len(sensor_status) - len(ng_sensors),
            "sensors_ng":   ng_sensors,
            "wifi_attempts": last_wifi_attempts,
            "uptime_min":   uptime_min,
        })
        client.publish("solar-heat/{}/status".format(zone), payload)
        client.disconnect()
        print("[Status] sd={} sensors_ng={} uptime={}min".format(
            sd_status, ng_sensors, uptime_min))
    except Exception as e:
        print("[Status] ERROR:", e)


# --- 電源監視 ---
def read_bus_voltage():
    adc_v = adc_power.read_u16() / 65535 * 3.3
    return adc_v * 2


def send_power_alert(bus_v):
    if not MQTT_AVAILABLE:
        return
    try:
        zone   = config.ZONE
        client = MQTTClient("pico_{}_alert".format(zone), config.MQTT_BROKER, port=config.MQTT_PORT)
        client.connect()
        payload = ujson.dumps({"zone": zone, "bus_v": round(bus_v, 2), "alert": "main_power_lost"})
        client.publish("solar-heat/{}/power_alert".format(zone), payload)
        client.disconnect()
        print("[PowerAlert] sent bus_v={}V".format(round(bus_v, 2)))
    except Exception as e:
        print("[PowerAlert] ERROR:", e)


# --- 起動 ---
wifi_off()

# SDマウント。失敗してもraiseしない（センサー測定とMQTT送信は続ける）
if mount_sd():
    print("[Boot] SD mounted OK")
else:
    print("[Boot] SD mount failed - continuing without SD logging")

# 初期LED状態を反映（起動時SD失敗時は即点滅）
bus_v_initial = read_bus_voltage()
set_led_state(
    power_alert=(bus_v_initial < POWER_THRESHOLD_V),
    sd_alert=(sd_status != "ok"),
)

# 初回のみNTP同期
if connect_wifi():
    sync_ntp()
    wifi_off()


# --- メインループ ---
while True:
    wifi_off()
    ts    = jst_time()
    data  = read_sensors()
    bus_v = read_bus_voltage()
    print(ts[:6], data, "bus={}V".format(round(bus_v, 2)))

    # SDヘルスチェック付き書き込み
    log_to_sd_with_recovery(ts, data)

    # アラート状態を判定してLED反映
    power_alert = bus_v < POWER_THRESHOLD_V
    sd_alert    = sd_status not in ("ok", "ok_after_remount")
    set_led_state(power_alert, sd_alert)

    # WiFi ON → 送信 → WiFi OFF
    if connect_wifi():
        ok_mqtt    = send_mqtt(ts, data)
        ok_ambient = send_ambient(data)
        send_status(ts, bus_v)
        if power_alert:
            print("[PowerAlert] bus={}V < {}V".format(round(bus_v, 2), POWER_THRESHOLD_V))
            send_power_alert(bus_v)
        wifi_off()
        if ok_mqtt or ok_ambient:
            blink_tx(2)
    else:
        print("WiFi unavailable - SD only")
        wifi_off()

    time.sleep(INTERVAL_SEC)

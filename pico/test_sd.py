"""SDカード動作確認テスト
1. カード検出 (GP6)
2. SPIマウント (GP2-5)
3. 書き込み・読み取り
4. ファイル一覧
"""
import machine
import os
import sdcard

PIN_SD_SCK    = 2
PIN_SD_MOSI   = 3
PIN_SD_MISO   = 4
PIN_SD_CS     = 5
PIN_SD_DETECT = 6

# WiFi干渉を避ける
import network
network.WLAN(network.STA_IF).active(False)

print("=== SD Card Test ===")

# 1. カード検出
detect = machine.Pin(PIN_SD_DETECT, machine.Pin.IN, machine.Pin.PULL_UP)
print("[1] Card Detect: GP6 =", detect.value(), "(0=挿入済み, 1=未挿入)")
if detect.value() != 0:
    print("    ERROR: カードが検出されません")
    raise SystemExit

# 2. SPI接続・マウント
print("[2] SPIマウント試行...")
try:
    spi = machine.SPI(0,
        sck=machine.Pin(PIN_SD_SCK),
        mosi=machine.Pin(PIN_SD_MOSI),
        miso=machine.Pin(PIN_SD_MISO))
    sd = sdcard.SDCard(spi, machine.Pin(PIN_SD_CS))
    os.mount(os.VfsFat(sd), "/sd")
    print("    OK: マウント成功")
except Exception as e:
    print("    ERROR:", e)
    raise SystemExit

# 3. 書き込み・読み取り
print("[3] 書き込みテスト...")
test_path = "/sd/_picobox_test.txt"
test_data = "PicoBox SD test OK"
try:
    with open(test_path, "w") as f:
        f.write(test_data)
    with open(test_path, "r") as f:
        readback = f.read()
    if readback == test_data:
        print("    OK: 書き込み・読み取り一致")
    else:
        print("    NG: 不一致 -> ", readback)
except Exception as e:
    print("    ERROR:", e)

# 4. ファイル一覧
print("[4] /sd ファイル一覧:")
for f in os.listdir("/sd"):
    try:
        st = os.stat("/sd/" + f)
        print("    {:10d}  {}".format(st[6], f))
    except:
        print("    ?           ", f)

# テストファイル削除
try:
    os.remove(test_path)
    print("    (テストファイル削除)")
except:
    pass

os.umount("/sd")
print("=== END ===")

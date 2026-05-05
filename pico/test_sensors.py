"""DS18B20 センサー動作確認テスト（7本一括）"""
import machine
import onewire
import ds18x20
import time

SENSOR_PINS = {
    8:  "S1_center_10cm",
    9:  "S2_center_25cm",
    10: "S3_center_40cm",
    11: "S4_edge_10cm",
    12: "S5_edge_25cm",
    13: "S6_edge_40cm",
    14: "S7_outdoor",
}

print("=== DS18B20 Sensor Test ===")

instances = {}
for pin_num, label in SENSOR_PINS.items():
    try:
        ow = onewire.OneWire(machine.Pin(pin_num))
        ds = ds18x20.DS18X20(ow)
        roms = ds.scan()
        if not roms:
            print("[GP{:2d}] {:18s} -> NO SENSOR".format(pin_num, label))
            continue
        ds.convert_temp()
        instances[pin_num] = (ds, roms[0], label)
    except Exception as e:
        print("[GP{:2d}] {:18s} -> SCAN ERROR: {}".format(pin_num, label, e))

time.sleep_ms(750)

print("--- 読み取り結果 ---")
ok_count = 0
for pin_num in sorted(SENSOR_PINS):
    label = SENSOR_PINS[pin_num]
    if pin_num not in instances:
        continue
    ds, rom, _ = instances[pin_num]
    try:
        temp = ds.read_temp(rom)
        rom_hex = "".join("{:02x}".format(b) for b in rom)
        print("[GP{:2d}] {:18s} = {:6.2f} degC  (ROM: {})".format(pin_num, label, temp, rom_hex))
        ok_count += 1
    except Exception as e:
        print("[GP{:2d}] {:18s} -> READ ERROR: {}".format(pin_num, label, e))

print("--- 結果: {}/{} 本 OK ---".format(ok_count, len(SENSOR_PINS)))

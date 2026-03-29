# scan_ids.py
# DS18B20 センサーIDを確認するユーティリティ
# Thonny で実行してシリアル出力でIDを確認 → config.py に転記
#
# 使い方:
#   1. センサーを1本ずつ接続しながら実行してIDを記録する
#   2. または全本接続して一覧取得後、温度値で判別する

import machine
import onewire
import ds18x20
import time

PIN_BUS1 = 21  # 中央地点バス
PIN_BUS2 = 22  # エッジ地点バス

for pin_num, label in [(PIN_BUS1, "BUS1(GP21) 中央"), (PIN_BUS2, "BUS2(GP22) エッジ")]:
    ow  = onewire.OneWire(machine.Pin(pin_num))
    ds  = ds18x20.DS18X20(ow)
    roms = ds.scan()
    print("=== {} : {} 個検出 ===".format(label, len(roms)))
    ds.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        id_str = ''.join(['{:02x}'.format(b) for b in rom])
        temp   = ds.read_temp(rom)
        print("  ID: {}  temp: {:.2f} C".format(id_str, temp))
    print()

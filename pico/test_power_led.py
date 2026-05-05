"""電源監視 + 赤LED連動テスト（高速ループ）
SDやWiFiは使わず、ADCとLEDだけで動作確認。
"""
import machine
import time

POWER_THRESHOLD_V = 4.0

adc = machine.ADC(26)
led = machine.Pin(15, machine.Pin.OUT)

print("Power monitor test (Ctrl+C to stop)")
while True:
    bus_v = adc.read_u16() / 65535 * 3.3 * 2
    if bus_v < POWER_THRESHOLD_V:
        led.on()
        state = "ALERT"
    else:
        led.off()
        state = "OK"
    print("bus={:.2f}V  {}".format(bus_v, state))
    time.sleep(1)

# センサー台帳

最終更新: 2026-07-19

## 設計変更（2026-04-02）
1-Wireバス方式（GP7共有）から**個別GPIO方式**（GP8〜GP14）に変更。
IDスキャン・sensor_map.json廃止。GPIOピン番号がそのまま位置情報になる。

## 圃場配置時の入れ替え（2026-07-19）

配線の取り回しの都合で、PicoBoxの筐体とエリアの対応を入れ替えた。

| PicoBox基板 | ファームウェア ZONE | 実際の設置エリア |
|---|---|---|
| Pico1（区A用に製作） | `zone-a` | **エリアC（微生物養生）** |
| Pico2（区B用に製作） | `zone-b` | エリアB（標準養生）※変更なし |
| Pico3（区C用に製作） | `zone-c` | **エリアA（対照区）** |

> ファームウェアは変更しない。`mqtt_logger.py` の `ZONE_REMAP` で受信時にゾーン名を変換するため、
> DB上は常に物理エリアと一致する（zone-a = エリアA、zone-c = エリアC）。

加えてセンサープローブも一部交換した。

| 交換内容 | 交換元 | 交換先 |
|---|---|---|
| No.21 ↔ No.2  | Pico3 GP8/J8 (center 10cm) | Pico3 GP10/J2 (center 40cm) |
| No.18 ↔ No.20 | Pico3 GP12/J4 (edge 25cm)  | Pico3 GP13/J5 (edge 40cm) |
| No.14 ↔ No.12 | Pico2 GP8/J8 (center 10cm) | Pico2 GP10/J2 (center 40cm) |

---

## Pico1 → エリアC（微生物養生）【DB: zone-c】

| GPIO | コネクタ | センサーNo. | センサーラベル | 割当 | DS18B20 ID | 確認温度 |
|---|---|---|---|---|---|---|
| GP8  | J8 | No.8  | S1_center_10cm | 中央 10cm   | 28abe15800000069 | 25.00°C |
| GP9  | J7 | No.7  | S2_center_25cm | 中央 25cm   | 28674ec00000002a | 24.94°C |
| GP10 | J2 | No.10 | S3_center_40cm | 中央 40cm   | 28d8574600000056 | 24.94°C |
| GP11 | J3 | No.3  | S4_edge_10cm   | エッジ 10cm | 2899fd3400000035 | 25.94°C |
| GP12 | J4 | No.4  | S5_edge_25cm   | エッジ 25cm | 28ef213400000060 | 25.06°C |
| GP13 | J5 | No.9  | S6_edge_40cm   | エッジ 40cm | 28e80f34000000bf | 25.13°C |
| GP14 | J6 | No.6  | S7_outdoor     | 外気温      | 2866a758000000c9 | 25.00°C |

---

## Pico2 → エリアB（標準養生）【DB: zone-b】

センサーNo.14 と No.12 を交換済み。

| GPIO | コネクタ | センサーNo. | センサーラベル | 割当 | DS18B20 ID |
|---|---|---|---|---|---|
| GP8  | J8 | **No.12** | S1_center_10cm | 中央 10cm   | 未取得 |
| GP9  | J7 | No.13 | S2_center_25cm | 中央 25cm   | 未取得 |
| GP10 | J2 | **No.14** | S3_center_40cm | 中央 40cm   | 未取得 |
| GP11 | J3 | No.11 | S4_edge_10cm   | エッジ 10cm | 未取得 |
| GP12 | J4 | No.15 | S5_edge_25cm   | エッジ 25cm | 未取得 |
| GP13 | J5 | No.16 | S6_edge_40cm   | エッジ 40cm | 未取得 |
| GP14 | J6 | No.17 | S7_outdoor     | 外気温      | 未取得 |

---

## Pico3 → エリアA（対照区）【DB: zone-a】

センサーNo.21 ↔ No.2、No.18 ↔ No.20 を交換済み。

| GPIO | コネクタ | センサーNo. | センサーラベル | 割当 | DS18B20 ID |
|---|---|---|---|---|---|
| GP8  | J8 | **No.2**  | S1_center_10cm | 中央 10cm   | 未取得 |
| GP9  | J7 | No.1  | S2_center_25cm | 中央 25cm   | 未取得 |
| GP10 | J2 | **No.21** | S3_center_40cm | 中央 40cm   | 未取得 |
| GP11 | J3 | No.19 | S4_edge_10cm   | エッジ 10cm | 未取得 |
| GP12 | J4 | **No.20** | S5_edge_25cm   | エッジ 25cm | 未取得 |
| GP13 | J5 | **No.18** | S6_edge_40cm   | エッジ 40cm | 未取得 |
| GP14 | J6 | No.36 | S7_outdoor     | 外気温      | 未取得 |

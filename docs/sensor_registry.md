# センサー台帳

最終更新: 2026-07-28

## ラベル変更（2026-07-28）

| 変更前 | 変更後 | 理由 |
|---|---|---|
| `S1_center_10cm` | `S1_center_15cm` | 実際の埋設深さは15cm。従来のラベルが誤り（過去データも15cm） |
| `S4_edge_10cm` | `S4_edge_15cm` | 同上 |
| `S7_outdoor`（区A・区Bのみ） | `S7_soil_5cm` | 外気温の測定価値が低かったため、土壌5cm深さに差し替え（2026-07-28 08:50 JST） |

- 区C（ユニット1）の GP14 は **外気温のまま**。
- `S7_soil_5cm` は BLOF公式の基準深さ（5cm）に相当するが、今回は途中からの計測で条件が揃わないため **参考値扱い**。積算温度の計算には含めない。
- DBの既存レコードも上記ラベルに UPDATE 済み（GCE・Raspberry Pi 両方）。データの削除はしていない。

## 設計変更（2026-04-02）
1-Wireバス方式（GP7共有）から**個別GPIO方式**（GP8〜GP14）に変更。
IDスキャン・sensor_map.json廃止。GPIOピン番号がそのまま位置情報になる。

## ファームウェア更新（2026-07-20）

筐体入れ替え・プローブ差し替えへの対応方式を変更。

| 変更前 | 変更後 |
|---|---|
| サーバー側 `ZONE_REMAP` / `LABEL_REMAP` で受信時に変換 | Pico の `config.py` に `ZONE` と `SENSOR_PINS` を正しく設定 |

各Picoが正しいゾーン名・正しいセンサーラベルで送信するため、サーバー側の変換は不要になった。
ウォッチドッグタイマー（8秒）も同時に追加。

---

## ユニット3 → 区A（標準区）【ZONE: zone-a】

config: `config_pico3.py`
プローブ入替: GP8⇔GP10（中央15cm⇔40cm）、GP12⇔GP13（端部25cm⇔40cm）

| GPIO | コネクタ | センサーNo. | config SENSOR_PINS | 実際の深さ |
|---|---|---|---|---|
| GP8  | J8 | No.2  | S3_center_40cm | 中央 40cm |
| GP9  | J7 | No.1  | S2_center_25cm | 中央 25cm |
| GP10 | J2 | No.21 | S1_center_15cm | 中央 15cm |
| GP11 | J3 | No.19 | S4_edge_15cm   | 端部 15cm |
| GP12 | J4 | No.20 | S6_edge_40cm   | 端部 40cm |
| GP13 | J5 | No.18 | S5_edge_25cm   | 端部 25cm |
| GP14 | J6 | No.36 | S7_soil_5cm    | 土壌 5cm（参考値） |

---

## ユニット2 → 区B（対照・菌なし）【ZONE: zone-b】

config: `config_pico2.py`
プローブ入替: GP8⇔GP10（中央15cm⇔40cm）

| GPIO | コネクタ | センサーNo. | config SENSOR_PINS | 実際の深さ |
|---|---|---|---|---|
| GP8  | J8 | No.12 | S3_center_40cm | 中央 40cm |
| GP9  | J7 | No.13 | S2_center_25cm | 中央 25cm |
| GP10 | J2 | No.14 | S1_center_15cm | 中央 15cm |
| GP11 | J3 | No.11 | S4_edge_15cm   | 端部 15cm |
| GP12 | J4 | No.15 | S5_edge_25cm   | 端部 25cm |
| GP13 | J5 | No.16 | S6_edge_40cm   | 端部 40cm |
| GP14 | J6 | No.17 | S7_soil_5cm    | 土壌 5cm（参考値） |

---

## ユニット1 → 区C（対照・ビニールなし）【ZONE: zone-c】

config: `config_pico1.py`
プローブ入替: なし（デフォルトのSENSOR_PINS使用）

| GPIO | コネクタ | センサーNo. | ラベル（デフォルト） | 実際の深さ | DS18B20 ID |
|---|---|---|---|---|---|
| GP8  | J8 | No.8  | S1_center_15cm | 中央 15cm | 28abe15800000069 |
| GP9  | J7 | No.7  | S2_center_25cm | 中央 25cm | 28674ec00000002a |
| GP10 | J2 | No.10 | S3_center_40cm | 中央 40cm | 28d8574600000056 |
| GP11 | J3 | No.3  | S4_edge_15cm   | 端部 15cm | 2899fd3400000035 |
| GP12 | J4 | No.4  | S5_edge_25cm   | 端部 25cm | 28ef213400000060 |
| GP13 | J5 | No.9  | S6_edge_40cm   | 端部 40cm | 28e80f34000000bf |
| GP14 | J6 | No.6  | S7_outdoor     | 外気温    | 2866a758000000c9 |

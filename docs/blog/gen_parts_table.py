"""PicoBox 部品表を画像として出力"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 日本語フォント設定（Windows標準のMeiryoまたはYu Gothic）
for font_name in ["Meiryo", "Yu Gothic", "MS Gothic", "Noto Sans CJK JP"]:
    if any(font_name in f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.family"] = font_name
        break

rows = [
    ["A1",        "Raspberry Pi Pico W",      "SC0918（ソケット経由）"],
    ["U1",        "LDO レギュレーター",       "MCP1703-3302E/DB（SOT-223）"],
    ["F1",        "リセッタブルヒューズ",     "MF-R050（500mA）"],
    ["D1",        "TVSダイオード",            "P6KE6.8CA-TB（双方向）"],
    ["D2",        "LED 黄緑",                 "3mm 570nm（電源表示）"],
    ["D3",        "LED 赤",                   "3mm 625nm（TX表示）"],
    ["SW1",       "スライドスイッチ",         "SS-12SDP2"],
    ["C1",        "セラミックコンデンサ",     "100nF（LDO入力バイパス）"],
    ["C2",        "セラミックコンデンサ",     "100nF（LDO出力バイパス）"],
    ["C3",        "電解コンデンサ",           "10µF / 50V（LDO出力安定）"],
    ["C4",        "電解コンデンサ",           "100µF / 35V（バルクデカップリング）"],
    ["J1",        "電源入力端子台",           "Phoenix SPTAF 2P 3.5mm"],
    ["J2〜J8",    "DS18B20コネクタ",          "JST PH 3P × 7本"],
    ["J9",        "SDカードソケット",         "1×10 メスピンソケット"],
    ["R2・R3",    "LED電流制限抵抗",          "330Ω × 2本（D2・D3用）"],
    ["R5・R6",    "分圧抵抗",                 "10kΩ × 2本（主電源監視 GP26）"],
    ["R7〜R13",   "DS18B20プルアップ抵抗",    "4.7kΩ × 7本"],
]
headers = ["参照記号", "部品", "値 / 型番"]

fig, ax = plt.subplots(figsize=(11, len(rows) * 0.42 + 1))
ax.axis("off")

table = ax.table(
    cellText=rows,
    colLabels=headers,
    cellLoc="left",
    colLoc="center",
    loc="center",
    colWidths=[0.13, 0.27, 0.50],
)
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 1.6)

# ヘッダ装飾
for j in range(len(headers)):
    cell = table[(0, j)]
    cell.set_facecolor("#2c3e50")
    cell.set_text_props(color="white", weight="bold")
    cell.set_height(0.06)

# 参照記号列を太字＋薄背景
for i in range(1, len(rows) + 1):
    table[(i, 0)].set_text_props(weight="bold")
    if i % 2 == 0:
        for j in range(len(headers)):
            table[(i, j)].set_facecolor("#f5f5f5")

# 左パディング
for i in range(len(rows) + 1):
    for j in range(len(headers)):
        table[(i, j)].PAD = 0.04

plt.title("PicoBox 部品表（1台分）", fontsize=14, weight="bold", pad=12)

out_path = os.path.join(os.path.dirname(__file__), "fig_parts_table.png")
plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
print("saved:", out_path)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import numpy as np

# Windows日本語フォント
for font in ["Yu Gothic", "Meiryo", "MS Gothic"]:
    try:
        plt.rcParams["font.family"] = font
        break
    except Exception:
        continue

fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

# 横軸: 月（6月〜10月）
months = ["6月", "7月", "8月", "9月", "10月"]
month_positions = [0, 1, 2, 3, 4]

# タスク定義 [名称, 開始(月単位), 終了(月単位), 色]
tasks = [
    ("土壌診断①\n（ベースライン）", 0.0,  1.0,  "#4E9A8A"),
    ("ビニール被覆・\n養生開始",       1.5,  2.0,  "#E07B54"),
    ("地温\n自動記録",                 1.5,  3.0,  "#5B8DB8"),
    ("土壌診断②\n（養生直後）",       3.0,  4.0,  "#4E9A8A"),
]

y_positions = list(range(len(tasks)))

bar_height = 0.5

for i, (label, start, end, color) in enumerate(tasks):
    ax.barh(i, end - start, left=start, height=bar_height,
            color=color, alpha=0.85, edgecolor="white", linewidth=1.5)
    # バーの中央にラベル
    mid = start + (end - start) / 2
    ax.text(mid, i, label, ha="center", va="center",
            fontsize=8.5, color="white", fontweight="bold", linespacing=1.4)

# 軸設定
ax.set_yticks([])
ax.set_xticks(month_positions)
ax.set_xticklabels(months, fontsize=12)
ax.set_xlim(-0.2, 4.5)
ax.set_ylim(-0.6, len(tasks) - 0.4)
ax.invert_yaxis()

# 月の区切り線
for x in month_positions:
    ax.axvline(x, color="#CCCCCC", linewidth=0.8, linestyle="--", zorder=0)

# タイトル
ax.set_title("実験スケジュール（2026年）", fontsize=14, fontweight="bold",
             pad=14, color="#333333")

# 枠線を最小限に
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#CCCCCC")
ax.tick_params(axis="x", colors="#555555")

plt.tight_layout()
plt.savefig("C:/Users/momon/work/solar-heat/docs/blog/schedule_gantt.png",
            dpi=150, bbox_inches="tight")
print("Done")

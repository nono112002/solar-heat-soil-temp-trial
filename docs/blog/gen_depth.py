import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

for font in ["Yu Gothic", "Meiryo", "MS Gothic"]:
    try:
        plt.rcParams["font.family"] = font
        break
    except Exception:
        continue

fig, ax = plt.subplots(figsize=(8, 7))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")
ax.axis("off")
ax.set_aspect("equal")

# --- ビニール ---
vinyl = mpatches.FancyBboxPatch((0.5, 8.8), 6.0, 0.35,
    boxstyle="round,pad=0.05",
    facecolor="#C8E6C9", edgecolor="#66BB6A", linewidth=2)
ax.add_patch(vinyl)
ax.text(3.5, 8.975, "ビニールフィルム", ha="center", va="center",
        fontsize=10, color="#2E7D32", fontweight="bold")

# --- 土層（地表〜50cm）---
soil = mpatches.FancyBboxPatch((0.5, 3.5), 6.0, 5.3,
    boxstyle="square,pad=0",
    facecolor="#D7B899", edgecolor="#A0785A", linewidth=1.5)
ax.add_patch(soil)

# 地表線
ax.plot([0.5, 6.5], [8.8, 8.8], color="#A0785A", linewidth=2)
ax.text(6.7, 8.8, "地表", va="center", fontsize=12, color="#333333", fontweight="bold")

# --- 深さ目盛り ---
depths = {10: 7.8, 25: 6.3, 40: 4.8}
depth_colors = ["#E07B54", "#C0504D", "#8B1A1A"]
labels = ["10cm", "25cm", "40cm"]

for i, (depth, y) in enumerate(depths.items()):
    # 水平点線
    ax.plot([0.5, 6.5], [y, y], color="#C8A882", linewidth=0.8,
            linestyle="--", zorder=1)
    # 深さラベル（左）
    ax.text(0.3, y, f"{depth}cm", ha="right", va="center",
            fontsize=10, color="#555555")

# --- センサー本体（縦棒）---
sensor_x = 3.5
# 地表からS3まで棒
ax.plot([sensor_x, sensor_x], [8.8, 4.8], color="#888888",
        linewidth=3, zorder=3, solid_capstyle="round")

# 各深さに●センサー
for i, (depth, y) in enumerate(depths.items()):
    ax.plot(sensor_x, y, "o", markersize=16, color=depth_colors[i],
            zorder=5, markeredgecolor="white", markeredgewidth=1.5)
    ax.text(sensor_x + 0.5, y, f"S（{depth}cm）", va="center",
            fontsize=10, color=depth_colors[i], fontweight="bold")


ax.set_xlim(-0.5, 8.0)
ax.set_ylim(3.0, 10.5)
ax.set_title("センサー設置深度（断面図）", fontsize=14, fontweight="bold",
             pad=12, color="#333333")

plt.tight_layout()
plt.savefig("C:/Users/momon/work/solar-heat/docs/blog/fig_depth.png",
            dpi=150, bbox_inches="tight")
print("Done: fig_depth.png")

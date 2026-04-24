import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm

for font in ["Yu Gothic", "Meiryo", "MS Gothic"]:
    try:
        plt.rcParams["font.family"] = font
        break
    except Exception:
        continue

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")
ax.set_aspect("equal")
ax.axis("off")

# 区画の定義 [x, y, 幅, 高さ, ラベル, 色, 説明]
zones = [
    (0.5, 0.5, 3.0, 4.5, "区A", "#E8F4E8", "太陽熱養生のみ\n（対照区）"),
    (4.0, 0.5, 3.0, 4.5, "区B", "#FFF4E8", "養生＋有機物"),
    (7.5, 0.5, 3.0, 4.5, "区C", "#E8F0F8", "養生＋有機物\n＋微生物資材"),
]

for (x, y, w, h, label, color, desc) in zones:
    # 区画の背景
    rect = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.1",
        facecolor=color, edgecolor="#999999", linewidth=1.5)
    ax.add_patch(rect)

    # 区名
    ax.text(x + w/2, y + h + 0.25, label, ha="center", va="bottom",
            fontsize=14, fontweight="bold", color="#333333")

    # 説明
    ax.text(x + w/2, y + h - 0.5, desc, ha="center", va="top",
            fontsize=9, color="#555555", linespacing=1.6)

    cx = x + w / 2       # 中央x
    ex_l = x + 0.35      # エッジ左x
    ex_r = x + w - 0.35  # エッジ右x
    sy = y + 2.0          # センサーy位置

    # 中央センサー（●）
    ax.plot(cx, sy, "o", markersize=14, color="#E07B54", zorder=5)
    ax.text(cx, sy - 0.45, "中央", ha="center", va="top",
            fontsize=8, color="#E07B54", fontweight="bold")

    # エッジセンサー右のみ
    ax.plot(ex_r, sy, "o", markersize=14, color="#5B8DB8", zorder=5)
    ax.text(ex_r, sy - 0.45, "エッジ", ha="center", va="top",
            fontsize=8, color="#5B8DB8", fontweight="bold")



ax.set_xlim(-0.2, 12.0)
ax.set_ylim(-1.0, 6.0)
ax.set_title("実験区画とセンサー配置（上面図）", fontsize=14, fontweight="bold",
             pad=12, color="#333333")

plt.tight_layout()
plt.savefig("C:/Users/momon/work/solar-heat/docs/blog/fig_zones.png",
            dpi=150, bbox_inches="tight")
print("Done: fig_zones.png")

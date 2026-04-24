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

fig, ax = plt.subplots(figsize=(16, 11))
fig.patch.set_facecolor("#F4F4F4")
ax.set_facecolor("#F4F4F4")
ax.axis("off")

# =============================================================
# ヘルパー
# =============================================================
def box(ax, x, y, w, h, line1, line2="", fc="#FFF", ec="#555",
        lw=2.0, fs1=9.5, fs2=7.8):
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.12",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3)
    ax.add_patch(rect)
    cy = y + h / 2 + (0.14 if line2 else 0)
    ax.text(x + w/2, cy, line1,
            ha="center", va="center", fontsize=fs1,
            fontweight="bold", color="#222", zorder=4)
    if line2:
        ax.text(x + w/2, y + h/2 - 0.18, line2,
                ha="center", va="center", fontsize=fs2,
                color="#555", zorder=4)

def varrow(ax, x, y_start, y_end, color="#555", lw=1.8):
    ax.annotate("", xy=(x, y_end), xytext=(x, y_start),
        arrowprops=dict(arrowstyle="-|>", color=color,
                        lw=lw, mutation_scale=13), zorder=5)

def harrow(ax, x_start, x_end, y, color="#555", lw=1.8):
    ax.annotate("", xy=(x_end, y), xytext=(x_start, y),
        arrowprops=dict(arrowstyle="-|>", color=color,
                        lw=lw, mutation_scale=13), zorder=5)

def harrow_left(ax, x_start, x_end, y, color="#555", lw=1.8):
    """左向き（センサー→Pico W 等）"""
    ax.annotate("", xy=(x_end, y), xytext=(x_start, y),
        arrowprops=dict(arrowstyle="-|>", color=color,
                        lw=lw, mutation_scale=13), zorder=5)

def vline(ax, x, y1, y2, color="#555", lw=1.8):
    ax.plot([x, x], [y1, y2], color=color, lw=lw, zorder=2)

def hline(ax, x1, x2, y, color="#555", lw=1.8):
    ax.plot([x1, x2], [y, y], color=color, lw=lw, zorder=2)

def alabel(ax, x, y, text, color="#555", fs=7.5):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            color=color, zorder=6,
            bbox=dict(facecolor="#F4F4F4", edgecolor="none", pad=1.5))

# =============================================================
# カラー
# =============================================================
CP  = "#3A72B0"   # 電源：青
CL  = "#B03030"   # LDO：赤
CG  = "#2E8B57"   # Pico W：緑
CS  = "#5A8A20"   # センサー：黄緑
CSD = "#B08020"   # SD：オレンジ
CW  = "#6050A0"   # クラウド：紫
CPR = "#C07020"   # 保護：茶

# =============================================================
# 座標定義
# （全矢印は縦か横のみ、事前にクロス確認済み）
#
#  電源ゾーン  x: 0.2 〜 6.8
#  Pico W     x: 7.0 〜 11.5
#  データゾーン x: 12.0 〜 15.5
# =============================================================

# --- 電源チェーン（中央 x=3.0） ---
X_TRUNK = 3.0

# 5V入力  bottom-left=(1.5, 9.0)  w=3.0 h=0.75
box(ax, 1.5, 9.0, 3.0, 0.75, "5V 入力", "上流電源ボックスから",
    fc="#E6EEF8", ec=CP, lw=2.2)

# ロッカースイッチ  bottom-left=(1.5, 8.15)  w=3.0 h=0.60
box(ax, 1.5, 8.15, 3.0, 0.60, "ロッカースイッチ", "電源 ON / OFF",
    fc="#FFF0E8", ec=CPR, lw=2.0)

# ポリスイッチ  bottom-left=(1.5, 7.15)  w=3.0 h=0.75
box(ax, 1.5, 7.15, 3.0, 0.75, "ポリスイッチ", "過電流保護・自動復帰",
    fc="#FFF3E0", ec=CPR, lw=2.0)

# 5V → ロッカースイッチ（下向き）
varrow(ax, X_TRUNK, 9.0, 8.75, color=CP)

# ロッカースイッチ → ポリスイッチ（下向き）
varrow(ax, X_TRUNK, 8.15, 7.90, color=CP)

# ポリスイッチ → バス（下向き）
varrow(ax, X_TRUNK, 7.15, 7.0, color=CP)

# バスライン  y=7.0  x=0.5〜6.5
hline(ax, 0.5, 6.5, 7.0, color=CP, lw=2.2)

# --- バスからのドロップ ---
# MCP1703  x=3.3〜5.3  y=5.4〜6.2
box(ax, 3.3, 5.4, 2.0, 0.75, "MCP1703", "外部 3.3V（SD・センサー用）",
    fc="#FCE8E8", ec=CL, lw=2.0, fs1=9.0)
varrow(ax, 4.3, 7.0, 6.15, color=CL)   # バス → MCP1703

# TVSダイオード  x=5.4〜6.6  y=5.4〜6.2
box(ax, 5.4, 5.4, 1.2, 0.75, "TVS\nダイオード", "サージ保護",
    fc="#FFF3E0", ec=CPR, lw=2.0, fs1=8.5)
varrow(ax, 6.0, 7.0, 6.15, color=CPR)  # バス → TVS
# TVS → GND（下向き短線＋GNDラベル）
vline(ax, 6.0, 5.4, 5.0, color=CPR, lw=1.5)
ax.text(6.0, 4.85, "GND", ha="center", va="top", fontsize=8.0,
        color=CPR, fontweight="bold", zorder=6)

# 分圧回路  x=0.3〜2.7  y=4.2〜4.95
box(ax, 0.3, 4.2, 2.4, 0.75, "分圧回路（GP26）",
    "5V→2.5V / 電池時→2.1V", fc="#FCE8E8", ec=CL, lw=2.0, fs1=8.5)
varrow(ax, 1.5, 7.0, 4.95, color=CL)   # バス → 分圧

# =============================================================
# Pico W
# =============================================================
box(ax, 7.0, 3.5, 4.5, 6.0, "Raspberry Pi\nPico W", "（マイコン）",
    fc="#E8F8F0", ec=CG, lw=2.5, fs1=12, fs2=9.5)

# VSYS（バス → Pico W）
# バスx=5.5から上へ y=7.5、そこから右へ Pico W へ
# ※ 幹x=3.0（ポリスイッチ矢印）と重ならないよう右側で分岐
vline(ax, 5.5, 7.0, 7.5, color=CP, lw=1.8)        # バスから上へ
harrow(ax, 5.5, 7.0, 7.5, color=CP)               # Pico W 左面へ
alabel(ax, 6.3, 7.65, "5V (VSYS)", color=CP)

# MCP1703 → Pico W
# MCP1703 下面 (4.3, 5.4) → 下へ y=4.8（TVS GND線 y=5.0〜5.4 を回避）→ 右へ x=7.0
vline(ax, 4.3, 5.4, 4.8, color=CL, lw=1.8)
hline(ax, 4.3, 7.0, 4.8, color=CL, lw=1.8)
# 矢印ヘッドは Pico W 左面に
ax.annotate("", xy=(7.0, 4.8), xytext=(6.8, 4.8),
    arrowprops=dict(arrowstyle="-|>", color=CL, lw=1.8, mutation_scale=13), zorder=5)
alabel(ax, 5.7, 4.95, "3.3V", color=CL)

# 分圧 → Pico W (GP26)
harrow(ax, 2.7, 7.0, 4.6, color=CL)
alabel(ax, 5.0, 4.75, "GP26（ADC）", color=CL)

# =============================================================
# データゾーン
# =============================================================

# DS18B20  y=7.1〜8.0
box(ax, 12.0, 7.1, 3.5, 0.85, "DS18B20 × 7本",
    "防水温度センサー（土中）",
    fc="#EEF8E8", ec=CS, lw=2.0)
# センサー → Pico W（左向き矢印）
harrow_left(ax, 12.0, 11.5, 7.55, color=CS)
alabel(ax, 11.75, 7.75, "GP8〜GP14", color=CS)

# SDカード  y=5.5〜6.35
box(ax, 12.0, 5.5, 3.5, 0.85, "SD カード",
    "ローカル記録",
    fc="#FFF8E8", ec=CSD, lw=2.0)
harrow(ax, 11.5, 12.0, 5.92, color=CSD)
alabel(ax, 11.75, 6.12, "GP2〜GP6", color=CSD)

# クラウド  y=3.9〜4.75
box(ax, 12.0, 3.9, 3.5, 0.85, "クラウド（Ambient）",
    "WiFi 送信",
    fc="#EEEAF8", ec=CW, lw=2.0)
harrow(ax, 11.5, 12.0, 4.33, color=CW)
alabel(ax, 11.75, 4.53, "WiFi", color=CW)

# =============================================================
# セクション見出し・タイトル
# =============================================================
ax.text(3.5, 10.3, "電源系統", ha="center", fontsize=11,
        color="#777", fontweight="bold")
ax.text(9.25, 10.3, "Pico W", ha="center", fontsize=11,
        color="#777", fontweight="bold")
ax.text(13.75, 10.3, "データ系統", ha="center", fontsize=11,
        color="#777", fontweight="bold")

# 区切り補助線
ax.axvline(6.8, color="#CCCCCC", lw=1.0, linestyle="--", zorder=1)
ax.axvline(11.7, color="#CCCCCC", lw=1.0, linestyle="--", zorder=1)

ax.set_xlim(0.0, 16.0)
ax.set_ylim(3.0, 10.8)
ax.set_title("PicoBox 回路構成図", fontsize=15, fontweight="bold",
             pad=14, color="#333")

plt.tight_layout()
plt.savefig("C:/Users/momon/work/solar-heat/docs/blog/fig_picobox_diagram.png",
            dpi=150, bbox_inches="tight")
print("Done")

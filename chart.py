"""
Chart generator — matplotlib for Telegram image output
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os, numpy as np
from config import MENU

# Try to use a font that supports Indonesian chars
plt.rcParams["font.family"] = "DejaVu Sans"

COLORS = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2E", "#44BBA4"]

def _prep_dir():
    d = os.path.expanduser("~/.dimsum_data/charts")
    os.makedirs(d, exist_ok=True)
    return d

def _save(fig, name):
    path = os.path.join(_prep_dir(), name)
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    return path

def bar_chart(summary, title="Penjualan Hari Ini"):
    """Bar chart: pcs per item"""
    items = summary["item_order"]
    pcs = [summary["per_item"][i]["pcs"] for i in items]
    rev = [summary["per_item"][i]["revenue"]/1000 for i in items]

    fig, ax1 = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax1.set_facecolor("#16213e")

    x = np.arange(len(items))
    bars = ax1.bar(x, pcs, color=COLORS[:len(items)], width=0.5, alpha=0.9)

    for bar, val in zip(bars, pcs):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 str(val), ha="center", va="bottom", fontsize=11,
                 fontweight="bold", color="white")

    ax1.set_xlabel("Menu", color="white", fontsize=10)
    ax1.set_ylabel("Terjual (pcs)", color="white", fontsize=10)
    ax1.set_title(title, color="white", fontsize=13, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(items, color="white", fontsize=9)
    ax1.tick_params(colors="white")
    ax1.spines["bottom"].set_color("#444")
    ax1.spines["left"].set_color("#444")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.set_ylim(0, max(pcs) * 1.2 + 1)

    return _save(fig, "bar_chart.png")

def pie_chart(summary, title="Kontribusi Revenue"):
    """Pie: revenue distribution"""
    items = summary["item_order"]
    values = [summary["per_item"][i]["revenue"] for i in items]
    labels = [f"{i}\n({v/1000:.0f}k)" for i, v in zip(items, values)]

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    fig.patch.set_facecolor("#1a1a2e")

    wedges, texts = ax.pie(values, labels=labels, colors=COLORS[:len(items)],
                           startangle=90, textprops={"color": "white", "fontsize": 9})
    ax.set_title(title, color="white", fontsize=12, fontweight="bold")

    return _save(fig, "pie_chart.png")

def profit_chart(summary, title="Profit per Item"):
    """Bar chart: profit comparison"""
    items = summary["item_order"]
    profits = [summary["per_item"][i]["profit"]/1000 for i in items]

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    x = np.arange(len(items))
    bars = ax.barh(x, profits, color=COLORS[:len(items)], height=0.5, alpha=0.9)

    for bar, val in zip(bars, profits):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f"Rp{val:.0f}k", ha="left", va="center",
                fontsize=10, color="white", fontweight="bold")

    ax.set_yticks(x)
    ax.set_yticklabels(items, color="white", fontsize=10)
    ax.set_xlabel("Profit (Rp ribu)", color="white", fontsize=10)
    ax.set_title(title, color="white", fontsize=12, fontweight="bold")
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return _save(fig, "profit_chart.png")

def trend_chart(daily_totals, title="Trend Penjualan"):
    """Line: daily trend"""
    dates = list(daily_totals.keys())
    values = list(daily_totals.values())

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    ax.plot(range(len(dates)), values, color="#44BBA4", linewidth=2.5,
            marker="o", markersize=6, markerfacecolor="#F18F01")

    for i, v in enumerate(values):
        ax.text(i, v + 0.5, str(v), ha="center", fontsize=9, color="white")

    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=30, color="white", fontsize=8)
    ax.set_ylabel("Pcs", color="white", fontsize=10)
    ax.set_title(title, color="white", fontsize=12, fontweight="bold")
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return _save(fig, "trend_chart.png")

"""Generate the graphical dashboard mockups (charts + stat cards)."""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

import ui
from data import build_all

OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)
DATA = build_all()

# Dashboard palette
DASH_BG = "#0b1220"
PANEL = "#0f172a"
GRID = "#1e293b"
LINE1 = "#14b8a6"   # teal
LINE2 = "#f59e0b"   # amber
LINE3 = "#60a5fa"   # blue


def _style_axes(ax) -> None:
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=ui.MUTED, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.7, alpha=0.8)
    ax.xaxis.label.set_color(ui.MUTED)
    ax.yaxis.label.set_color(ui.MUTED)


def _title_bar(fig, title: str, subtitle: str) -> None:
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.patch.set_facecolor(DASH_BG)
    ax.scatter(0.03, 0.955, s=120, color=LINE1)
    ax.text(0.055, 0.955, "MarketPulse", color=ui.TEXT, fontproperties=ui.SANS,
            fontsize=15, fontweight="bold", va="center")
    ax.text(0.055, 0.918, title, color=LINE1, fontproperties=ui.SANS,
            fontsize=12, va="center")
    ax.text(0.97, 0.945, subtitle, color=ui.MUTED, fontproperties=ui.SANS,
            fontsize=10.5, va="center", ha="right")
    ax.plot([0.03, 0.97], [0.895, 0.895], color=GRID, lw=1)


def _stat_card(fig, rect, label: str, value: str, colour: str = ui.TEXT) -> None:
    ax = fig.add_axes(rect)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(FancyBboxPatch((0.02, 0.06), 0.96, 0.88,
                 boxstyle="round,pad=0.02,rounding_size=0.06",
                 linewidth=1, edgecolor=GRID, facecolor=PANEL))
    ax.text(0.5, 0.66, value, color=colour, fontproperties=ui.SANS,
            fontsize=17, fontweight="bold", va="center", ha="center")
    ax.text(0.5, 0.28, label, color=ui.MUTED, fontproperties=ui.SANS,
            fontsize=10.5, va="center", ha="center")


def save(fig, name: str) -> None:
    fig.savefig(f"{OUT}/{name}", dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------------------
# 4. Crypto dashboard
# ---------------------------------------------------------------------------
def crypto_dashboard() -> None:
    d = DATA
    s = d["crypto_summary"]
    fig = plt.figure(figsize=(11.5, 8.0))
    _title_bar(fig, "BTC/USD  \u2014  30-day analytics", "source: crypto")

    ax = fig.add_axes([0.08, 0.14, 0.87, 0.56])
    _style_axes(ax)
    ax.plot(d["dates"], d["btc"], color=LINE1, lw=2.2, label="BTC/USD price")
    ax.plot(d["dates"], d["btc_ma"], color=LINE2, lw=2.0, ls="--",
            label="7-day moving average")
    ax.fill_between(d["dates"], d["btc"], d["btc"].min(), color=LINE1, alpha=0.08)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.set_ylabel("USD")
    leg = ax.legend(loc="upper left", frameon=False)
    for text in leg.get_texts():
        text.set_color(ui.TEXT)

    pct = s["pct_change"]
    pct_colour = "#22c55e" if pct >= 0 else "#ef4444"
    cards = [
        ("Last price", f"${s['last_value']:,.0f}", ui.TEXT),
        ("Min", f"${s['min_value']:,.0f}", ui.TEXT),
        ("Max", f"${s['max_value']:,.0f}", ui.TEXT),
        ("Change", f"{pct:+.2f}%", pct_colour),
    ]
    for i, (label, value, colour) in enumerate(cards):
        _stat_card(fig, [0.08 + i * 0.223, 0.72, 0.205, 0.16],
                   label, value, colour)
    save(fig, "04_crypto_dashboard.png")


# ---------------------------------------------------------------------------
# 6. Forex dashboard + correlation
# ---------------------------------------------------------------------------
def forex_dashboard() -> None:
    d = DATA
    fig = plt.figure(figsize=(11.5, 8.0))
    _title_bar(fig, "USD/EUR & USD/GBP  \u2014  correlation", "source: forex")

    ax1 = fig.add_axes([0.07, 0.14, 0.52, 0.66])
    _style_axes(ax1)
    ax1.plot(d["fx_dates"], d["eur"], color=LINE1, lw=2.2, label="USD/EUR")
    ax1.plot(d["fx_dates"], d["gbp"], color=LINE3, lw=2.2, label="USD/GBP")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax1.set_ylabel("rate")
    ax1.set_title("Daily FX rates", color=ui.TEXT, fontproperties=ui.SANS,
                  fontsize=12, loc="left")
    leg = ax1.legend(loc="upper left", frameon=False)
    for t in leg.get_texts():
        t.set_color(ui.TEXT)

    # Scatter with regression line
    ax2 = fig.add_axes([0.66, 0.14, 0.29, 0.66])
    _style_axes(ax2)
    ax2.scatter(d["eur"], d["gbp"], color=LINE2, s=36, alpha=0.85, zorder=3)
    m, b = np.polyfit(d["eur"], d["gbp"], 1)
    xs = np.linspace(d["eur"].min(), d["eur"].max(), 50)
    ax2.plot(xs, m * xs + b, color=ui.TEXT, lw=1.5, ls="--", alpha=0.7)
    ax2.set_xlabel("USD/EUR")
    ax2.set_ylabel("USD/GBP")
    ax2.set_title("Correlation", color=ui.TEXT, fontproperties=ui.SANS,
                  fontsize=12, loc="left")
    r = d["correlation"]["correlation"]
    ax2.text(0.05, 0.93, f"r = {r:.3f}", transform=ax2.transAxes,
             color=LINE1, fontproperties=ui.SANS, fontsize=15,
             fontweight="bold", va="top")
    ax2.text(0.05, 0.83, f"n = {d['correlation']['overlapping_points']} days",
             transform=ax2.transAxes, color=ui.MUTED, fontproperties=ui.SANS,
             fontsize=10, va="top")
    save(fig, "06_forex_dashboard.png")


# ---------------------------------------------------------------------------
# 8. CSV dashboard
# ---------------------------------------------------------------------------
def csv_dashboard() -> None:
    d = DATA
    prof = d["csv_profile_full"]
    fig = plt.figure(figsize=(11.5, 8.0))
    _title_bar(fig, "sales_data.csv  \u2014  data quality profile",
               "POST /datasets/upload")

    cards = [
        ("Rows", f"{prof['rows']:,}", ui.TEXT),
        ("Columns", str(prof["columns"]), ui.TEXT),
        ("Missing values", str(prof["missing_values"]), "#f59e0b"),
        ("Duplicate rows", str(prof["duplicate_rows"]), "#ef4444"),
    ]
    for i, (label, value, colour) in enumerate(cards):
        _stat_card(fig, [0.07 + i * 0.223, 0.70, 0.205, 0.17],
                   label, value, colour)

    # Nulls-per-column bar chart (only columns that have nulls)
    names = [c[0] for c in d["columns"] if c[2] > 0]
    nulls = [c[2] for c in d["columns"] if c[2] > 0]
    order = np.argsort(nulls)[::-1]
    names = [names[i] for i in order]
    nulls = [nulls[i] for i in order]

    ax = fig.add_axes([0.09, 0.11, 0.85, 0.5])
    _style_axes(ax)
    bars = ax.bar(names, nulls, color=LINE2, width=0.6)
    ax.set_ylabel("null count")
    ax.set_title("Missing values per column", color=ui.TEXT,
                 fontproperties=ui.SANS, fontsize=12, loc="left")
    ax.tick_params(axis="x", rotation=30)
    for bar, v in zip(bars, nulls):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.15, str(v),
                ha="center", va="bottom", color=ui.TEXT,
                fontproperties=ui.SANS, fontsize=9)
    save(fig, "08_csv_dashboard.png")


if __name__ == "__main__":
    crypto_dashboard()
    forex_dashboard()
    csv_dashboard()

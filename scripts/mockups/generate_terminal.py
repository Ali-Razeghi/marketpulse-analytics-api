"""Generate the terminal-style JSON mockups and the Swagger page."""

from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

import ui
from data import build_all

OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)
DATA = build_all()


def jlines(obj) -> list[str]:
    return json.dumps(obj, indent=2).splitlines()


def save(fig, name: str) -> None:
    fig.savefig(f"{OUT}/{name}", dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------------------
# 1. Swagger / OpenAPI docs page (browser mockup)
# ---------------------------------------------------------------------------
def swagger() -> None:
    endpoints = [
        ("auth", [
            ("POST", "/api/v1/auth/register", "Register a new user"),
            ("POST", "/api/v1/auth/login", "Log in with JSON body"),
            ("POST", "/api/v1/auth/token", "OAuth2 token (Swagger Authorize)"),
        ]),
        ("users", [
            ("GET", "/api/v1/users/me", "Get my profile"),
            ("PATCH", "/api/v1/users/me", "Update my profile"),
        ]),
        ("data-sources", [
            ("GET", "/api/v1/sources", "List available data sources"),
            ("POST", "/api/v1/ingest/{source_name}", "Fetch from a source and store"),
        ]),
        ("analytics", [
            ("GET", "/api/v1/data/series", "Read a raw stored series"),
            ("GET", "/api/v1/analytics/summary", "Descriptive statistics"),
            ("GET", "/api/v1/analytics/moving-average", "Rolling moving average"),
            ("GET", "/api/v1/analytics/correlation", "Correlation between two series"),
        ]),
        ("datasets", [
            ("POST", "/api/v1/datasets/upload", "Upload a CSV and profile it"),
        ]),
    ]

    fig = plt.figure(figsize=(11.5, 9.2))
    ui.draw_window(fig, title="MarketPulse Analytics API",
                   url="localhost:8000/docs")
    ax = fig.add_axes([0.04, 0.04, 0.92, 0.83])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(0, 97, "MarketPulse Analytics API", color=ui.TEXT,
            fontproperties=ui.SANS, fontsize=20, fontweight="bold", va="top")
    ax.text(0, 92.5, "0.1.0   OAS 3.1", color=ui.MUTED, fontproperties=ui.MONO,
            fontsize=11, va="top")
    ax.text(0, 89, "Multi-source data integration and analytics platform.",
            color=ui.MUTED, fontproperties=ui.SANS, fontsize=11.5, va="top")
    # Authorize button
    ax.add_patch(FancyBboxPatch((82, 90.5), 16, 5,
                 boxstyle="round,pad=0.3,rounding_size=1.2",
                 linewidth=1.3, edgecolor=ui.TEAL, facecolor="none"))
    ax.text(90, 93, "Authorize", color=ui.TEAL,
            fontproperties=ui.SANS, fontsize=11, va="center", ha="center")

    y = 84
    for tag, rows in endpoints:
        ax.text(0, y, tag, color=ui.TEXT, fontproperties=ui.SANS,
                fontsize=14, fontweight="bold", va="top")
        ax.plot([0, 100], [y - 2.4, y - 2.4], color=ui.BORDER, lw=0.8)
        y -= 5
        for method, path, summary in rows:
            colour = ui.METHOD_COLORS[method]
            ax.add_patch(FancyBboxPatch((0, y - 2.9), 11, 3.4,
                         boxstyle="round,pad=0.2,rounding_size=0.6",
                         linewidth=0, facecolor=colour))
            ax.text(5.5, y - 1.2, method, color="white", fontproperties=ui.SANS,
                    fontsize=9.5, fontweight="bold", va="center", ha="center")
            ax.add_patch(FancyBboxPatch((12.5, y - 3.0), 85.5, 3.6,
                         boxstyle="round,pad=0.15,rounding_size=0.6",
                         linewidth=1, edgecolor=ui.BORDER, facecolor="#111c2e"))
            ax.text(14.5, y - 1.2, path, color=ui.TEXT, fontproperties=ui.MONO,
                    fontsize=11, va="center", ha="left")
            ax.text(60, y - 1.2, summary, color=ui.MUTED, fontproperties=ui.SANS,
                    fontsize=10, va="center", ha="left")
            y -= 4.6
        y -= 1.5

    save(fig, "01_swagger_docs.png")


# ---------------------------------------------------------------------------
# 2. Auth flow (terminal)
# ---------------------------------------------------------------------------
def auth() -> None:
    tok = DATA["token"]
    lines = [
        "# 1) Register a new account",
        "$ curl -X POST localhost:8000/api/v1/auth/register \\",
        '      -d \'{"email":"me@example.com","password":"supersecret1"}\'',
        "",
        "HTTP/1.1 201 Created",
        "{",
        '  "id": 1,',
        '  "email": "me@example.com",',
        '  "full_name": null,',
        '  "role": "user",',
        '  "is_active": true,',
        '  "created_at": "2026-07-27T09:14:03Z"',
        "}",
        "",
        "# 2) Log in and receive a JWT access token",
        "$ curl -X POST localhost:8000/api/v1/auth/login \\",
        '      -d \'{"email":"me@example.com","password":"supersecret1"}\'',
        "",
        "HTTP/1.1 200 OK",
        "{",
        f'  "access_token": "{tok}",',
        '  "token_type": "bearer"',
        "}",
    ]
    size, rect = ui.fit_figure(lines, fontsize=12)
    fig = plt.figure(figsize=size)
    ui.draw_window(fig, title="Authentication  \u2014  register & login")
    ui.draw_json(fig, lines, rect=rect, fontsize=12)
    save(fig, "02_auth_flow.png")


# ---------------------------------------------------------------------------
# 3. Crypto analytics (terminal JSON)
# ---------------------------------------------------------------------------
def crypto_json() -> None:
    s = DATA["crypto_summary"]
    lines = [
        "# Ingest 30 days of BTC/USD from CoinGecko, then analyse",
        "$ curl -X POST localhost:8000/api/v1/ingest/crypto \\",
        '      -H "Authorization: Bearer $TOKEN" \\',
        '      -d \'{"coin_id":"bitcoin","vs_currency":"usd","days":30}\'',
        "",
        "HTTP/1.1 200 OK",
    ]
    lines += jlines({
        "source": "crypto",
        "series_keys": ["bitcoin/usd"],
        "points_ingested": 31,
    })
    lines += [
        "",
        "$ curl -G localhost:8000/api/v1/analytics/summary \\",
        '      -H "Authorization: Bearer $TOKEN" \\',
        '      --data-urlencode "source=crypto" \\',
        '      --data-urlencode "series_key=bitcoin/usd"',
        "",
        "HTTP/1.1 200 OK",
    ]
    lines += jlines(s)
    size, rect = ui.fit_figure(lines, fontsize=11.5)
    fig = plt.figure(figsize=size)
    ui.draw_window(fig, title="Crypto analytics  \u2014  ingest + summary")
    ui.draw_json(fig, lines, rect=rect, fontsize=11.5)
    save(fig, "03_crypto_json.png")


# ---------------------------------------------------------------------------
# 5. Forex + correlation (terminal JSON)
# ---------------------------------------------------------------------------
def forex_json() -> None:
    lines = [
        "# Ingest two FX series, then correlate them",
        "$ curl -X POST localhost:8000/api/v1/ingest/forex \\",
        '      -H "Authorization: Bearer $TOKEN" \\',
        '      -d \'{"base":"USD","symbol":"EUR","days":30}\'',
        "",
        "HTTP/1.1 200 OK",
    ]
    lines += jlines({
        "source": "forex",
        "series_keys": ["usd/eur"],
        "points_ingested": 22,
    })
    lines += [
        "",
        "$ curl -G localhost:8000/api/v1/analytics/correlation \\",
        '      -H "Authorization: Bearer $TOKEN" \\',
        '      --data-urlencode "source_a=forex" \\',
        '      --data-urlencode "series_key_a=usd/eur" \\',
        '      --data-urlencode "source_b=forex" \\',
        '      --data-urlencode "series_key_b=usd/gbp"',
        "",
        "HTTP/1.1 200 OK",
    ]
    lines += jlines(DATA["correlation"])
    size, rect = ui.fit_figure(lines, fontsize=11.5)
    fig = plt.figure(figsize=size)
    ui.draw_window(fig, title="Forex analytics  \u2014  ingest + correlation")
    ui.draw_json(fig, lines, rect=rect, fontsize=11.5)
    save(fig, "05_forex_json.png")


# ---------------------------------------------------------------------------
# 7. CSV upload profiling (terminal JSON)
# ---------------------------------------------------------------------------
def csv_json() -> None:
    lines = [
        "# Upload a CSV file and receive a structural + statistical profile",
        "$ curl -X POST localhost:8000/api/v1/datasets/upload \\",
        '      -H "Authorization: Bearer $TOKEN" \\',
        '      -F "file=@sales_data.csv"',
        "",
        "HTTP/1.1 200 OK",
    ]
    lines += jlines(DATA["csv_profile_short"])
    size, rect = ui.fit_figure(lines, fontsize=11.5)
    fig = plt.figure(figsize=size)
    ui.draw_window(fig, title="CSV dataset  \u2014  upload & profile")
    ui.draw_json(fig, lines, rect=rect, fontsize=11.5)
    save(fig, "07_csv_json.png")


if __name__ == "__main__":
    swagger()
    auth()
    crypto_json()
    forex_json()
    csv_json()

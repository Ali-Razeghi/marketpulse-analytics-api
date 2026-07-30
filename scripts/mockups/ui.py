"""Rendering toolkit for the mockups.

All images share one palette and one set of primitives so they look like a
coherent product. The tricky part is syntax-highlighted JSON with perfect
monospace alignment: we make one data-unit equal exactly one monospace glyph
advance, so tokens drawn separately still butt up cleanly.
"""

from __future__ import annotations

import re

import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BG = "#0b1220"          # page background (dark)
CARD = "#0f172a"        # terminal / window body
CARD_HEAD = "#1e293b"   # window title bar
BORDER = "#334155"
TEAL = "#14b8a6"        # FastAPI-ish brand accent
TEXT = "#e2e8f0"
MUTED = "#94a3b8"

# JSON token colours (dark theme)
C_KEY = "#7dd3fc"
C_STR = "#86efac"
C_NUM = "#fca5a5"
C_BOOL = "#c4b5fd"
C_PUNC = "#94a3b8"

# HTTP method badge colours
METHOD_COLORS = {
    "GET": "#2563eb",
    "POST": "#16a34a",
    "PATCH": "#d97706",
    "DELETE": "#dc2626",
}

MONO = fm.FontProperties(family="DejaVu Sans Mono")
SANS = fm.FontProperties(family="DejaVu Sans")

# DejaVu Sans Mono advance width as a fraction of the font size (em).
MONO_ADVANCE = 1233 / 2048  # ~0.602


def mono_char_inches(fontsize: float) -> float:
    """Width of one monospace character, in inches, at ``fontsize`` points."""
    return MONO_ADVANCE * fontsize / 72.0


# ---------------------------------------------------------------------------
# JSON highlighting
# ---------------------------------------------------------------------------
def _value_segments(text: str, col: int) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    sm = re.match(r'^"([^"]*)"(.*)$', text)
    if sm:
        s, tail = sm.groups()
        out.append((col, f'"{s}"', C_STR))
        if tail:
            out.append((col + len(s) + 2, tail, C_PUNC))
        return out
    nm = re.match(r"^(-?\d+\.?\d*)(.*)$", text)
    if nm:
        num, tail = nm.groups()
        out.append((col, num, C_NUM))
        if tail:
            out.append((col + len(num), tail, C_PUNC))
        return out
    bm = re.match(r"^(true|false|null)(.*)$", text)
    if bm:
        b, tail = bm.groups()
        out.append((col, b, C_BOOL))
        if tail:
            out.append((col + len(b), tail, C_PUNC))
        return out
    out.append((col, text, C_PUNC))
    return out


def highlight(line: str) -> list[tuple[int, str, str]]:
    """Return ``(column, text, colour)`` segments for one JSON line."""
    key_m = re.match(r'^(\s*)"([^"]*)"(\s*:\s*)(.*)$', line)
    if key_m:
        indent, key, colon, rest = key_m.groups()
        col = len(indent)
        segs = [(col, f'"{key}"', C_KEY), (col + len(key) + 2, colon, C_PUNC)]
        segs += _value_segments(rest, col + len(key) + 2 + len(colon))
        return segs
    indent = len(line) - len(line.lstrip(" "))
    return _value_segments(line[indent:], indent)


# ---------------------------------------------------------------------------
# Window chrome
# ---------------------------------------------------------------------------
def draw_window(fig, *, title: str, url: str | None = None) -> None:
    """Draw a rounded window/card with a title bar and traffic-light dots."""
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(BG)

    card = FancyBboxPatch(
        (0.012, 0.012), 0.976, 0.976,
        boxstyle="round,pad=0.006,rounding_size=0.02",
        linewidth=1.2, edgecolor=BORDER, facecolor=CARD, mutation_aspect=1,
    )
    ax.add_patch(card)

    head = FancyBboxPatch(
        (0.012, 0.90), 0.976, 0.088,
        boxstyle="round,pad=0.006,rounding_size=0.02",
        linewidth=0, facecolor=CARD_HEAD,
    )
    ax.add_patch(head)

    for i, colour in enumerate(("#ef4444", "#f59e0b", "#22c55e")):
        ax.scatter(0.035 + i * 0.022, 0.945, s=90, color=colour, zorder=5)

    if url is not None:
        ax.add_patch(
            FancyBboxPatch(
                (0.12, 0.925), 0.62, 0.04,
                boxstyle="round,pad=0.004,rounding_size=0.02",
                linewidth=1, edgecolor=BORDER, facecolor="#0b1220",
            )
        )
        ax.text(0.135, 0.945, url, color=MUTED, fontproperties=MONO,
                fontsize=11, va="center", ha="left")
        ax.text(0.965, 0.945, title, color=TEAL, fontproperties=SANS,
                fontsize=11, va="center", ha="right", fontweight="bold")
    else:
        ax.text(0.5, 0.945, title, color=TEXT, fontproperties=SANS,
                fontsize=12, va="center", ha="center", fontweight="bold")


def draw_json(fig, lines: list[str], *, rect, fontsize: float = 12.5) -> None:
    """Render highlighted JSON/terminal lines inside ``rect`` (figure fraction).

    Lines beginning with ``$`` are treated as shell prompts; lines beginning
    with ``#`` as comments.
    """
    ax = fig.add_axes(rect)
    ncols = max((len(ln) for ln in lines), default=1) + 1
    nrows = len(lines)
    ax.set_xlim(0, ncols)
    ax.set_ylim(nrows, 0)
    ax.axis("off")

    for row, line in enumerate(lines):
        y = row + 0.5
        if line.startswith("$"):
            ax.text(0, y, "$", color=TEAL, fontproperties=MONO,
                    fontsize=fontsize, va="center", ha="left", fontweight="bold")
            ax.text(2, y, line[2:], color=TEXT, fontproperties=MONO,
                    fontsize=fontsize, va="center", ha="left")
            continue
        if line.startswith("#"):
            ax.text(0, y, line, color=MUTED, fontproperties=MONO,
                    fontsize=fontsize, va="center", ha="left", style="italic")
            continue
        if line.startswith(("HTTP", "< HTTP")):
            ax.text(0, y, line, color="#fcd34d", fontproperties=MONO,
                    fontsize=fontsize, va="center", ha="left")
            continue
        for col, text, colour in highlight(line):
            ax.text(col, y, text, color=colour, fontproperties=MONO,
                    fontsize=fontsize, va="center", ha="left")


def fit_figure(lines: list[str], *, fontsize: float = 12.5,
               header_in: float = 0.95, side_in: float = 0.5,
               bottom_in: float = 0.45):
    """Compute a figure sized to fit ``lines`` exactly, and the code rect."""
    cw = mono_char_inches(fontsize)
    ncols = max((len(ln) for ln in lines), default=1) + 1
    nrows = len(lines)
    row_h = fontsize * 1.55 / 72.0
    code_w = ncols * cw
    code_h = nrows * row_h
    fig_w = side_in * 2 + code_w
    fig_h = header_in + code_h + bottom_in
    rect = [side_in / fig_w, bottom_in / fig_h, code_w / fig_w, code_h / fig_h]
    return (fig_w, fig_h), rect

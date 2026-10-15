"""House chart style for Data 4 The People (dark palette: background #181A1B, text #BBBDC0).

Series hues are the dataviz reference palette's dark steps. Yellow, blue and magenta are the
only three hues used together on one plot: that set clears the all-pairs gates on this
surface (scripts/validate_palette.py "#c98500,#3987e5,#d55181" dark "#181A1B" all). A fourth
series is drawn in gray and dashed, so it never relies on hue.
"""
import matplotlib as mpl

SURFACE = "#181A1B"
INK     = "#BBBDC0"
INK_DIM = "#8A9098"
MUTED   = "#6B7178"      # de-emphasis marks, 3.54:1 on the surface
GRID    = "#2A2D2F"

SULFUR  = "#c98500"      # yellow, slot 4
DIESEL  = "#3987e5"      # blue, slot 1
DAP     = "#d55181"      # magenta, slot 5
ACID    = INK            # gray, always dashed

CREDIT  = "Built by Data 4 The People"


def use_house_style():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK_DIM, "ytick.color": INK_DIM,
        "axes.edgecolor": GRID, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 11, "text.parse_math": False, "figure.dpi": 160, "savefig.dpi": 160,
    })


def titleblock(fig, title, subtitle=None, y=0.965):
    """Gap between title and subtitle is set in inches, so it looks the same on a short
    figure and a tall one."""
    fig.text(0.03, y, title, color=INK, fontsize=17, fontweight="bold", va="top", ha="left")
    if subtitle:
        gap = 0.36 / fig.get_figheight()
        fig.text(0.03, y - gap, subtitle, color=INK_DIM, fontsize=11, va="top", ha="left", linespacing=1.45)


def credit(fig, source):
    fig.text(0.03, 0.02, source, color=MUTED, fontsize=8.5, ha="left", va="bottom", linespacing=1.4)
    fig.text(0.97, 0.02, CREDIT, color=MUTED, fontsize=8.5, ha="right", va="bottom")

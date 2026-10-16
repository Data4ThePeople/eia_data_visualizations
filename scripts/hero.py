"""Hero for oil-draw-update: the weekly crude draws chart as a picture, not a figure.

Same bars and colors as images/01-weekly-crude-draws.png, but full frame with no axes or
fine print, and a short lockup on a backing panel inside the crop-safe band (Prismic's
square crop of a 1680x1080 keeps only x 0.18-0.82). Modeled on the SNAP_Locations
series heroes (src/analysis/hero.py). Every number is read from the same pull.

    python scripts/hero.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from plot_style import SURFACE, INK, INK_DIM, MUTED
from weekly_draws import fetch, numbers, WAR_START, COMM, SPR

OUT = "posts/oil-draw-update/images/oil-draw-update-hero-1680x1080.png"
W_PX, H_PX, DPI = 1680, 1080, 200
MONO = "DejaVu Sans Mono"
DIM = 0.45            # earlier weeks recede so this week's bar carries the frame


def main():
    w = fetch()
    d, n = numbers(w)
    war = d[d.index > WAR_START] / 1000
    x = list(range(len(war)))
    fig = plt.figure(figsize=(W_PX / DPI, H_PX / DPI), dpi=DPI, facecolor=SURFACE)
    ax = fig.add_axes([0.11, 0.07, 0.70, 0.86])   # right edge at 0.81 keeps the latest bar in the square crop
    ax.set_facecolor(SURFACE); ax.set_axis_off()
    pos = [0.0] * len(x); neg = [0.0] * len(x)
    for col, color in [("commercial", COMM), ("spr", SPR)]:
        for i, v in enumerate(war[col]):
            base = neg[i] if v < 0 else pos[i]
            ax.bar(i, v, width=0.72, bottom=base, color=color, alpha=1 if i == x[-1] else DIM,
                   edgecolor=SURFACE, linewidth=1.0, zorder=3)
            if v < 0: neg[i] += v
            else: pos[i] += v
    ax.axhline(0, color=MUTED, lw=1, zorder=2)
    ax.set_xlim(-0.8, x[-1] + 0.8)
    ax.set_ylim(-20.5, 46)      # headroom: bars sit low, the lockup sits above them with no overlap
    last = n["total_change"] / 1000
    ax.add_patch(plt.Rectangle((x[-1] - 0.62, last - 1.1), 1.24, -last + 2.2, fill=False, edgecolor=INK,
                               lw=1.8, joinstyle="round", zorder=6))
    ax.annotate("Oct. 9", (x[-1], last - 1.1), xytext=(0, -8), textcoords="offset points", ha="center", va="top",
                family=MONO, fontsize=12, color=INK, fontweight="bold", zorder=9)

    # lockup: kicker, headline number, what it is, legend; panel fitted to the measured text
    PT = DPI / 72 / H_PX
    block = [("OIL UPDATE", 11, INK_DIM, "normal", 1.6),
             (f"{-last:.1f} MILLION BARRELS", 22, COMM, "bold", 2.0),
             ("of commercial crude drawn in one week,", 12.5, INK, "normal", 1.8),
             ("the most since the war began", 12.5, INK, "normal", 1.45),
             ("legend", 10.5, None, "normal", 2.3)]
    LX = 0.205
    height = sum(sz * lead * PT for _, sz, _, _, lead in block)
    y = 0.95
    drawn = []
    for text, size, color, weight, lead in block:
        y -= size * lead * PT
        if color is None:      # legend line: two colored words
            t1 = fig.text(LX, y, "● commercial", family=MONO, fontsize=size, color=COMM, zorder=9)
            fig.canvas.draw()
            bb = t1.get_window_extent(fig.canvas.get_renderer())
            x2 = fig.transFigure.inverted().transform((bb.x1, 0))[0] + 0.025
            t2 = fig.text(x2, y, "● Strategic Petroleum Reserve", family=MONO, fontsize=size, color=SPR, zorder=9)
            drawn += [t1, t2]
        else:
            drawn.append(fig.text(LX, y, text, family=MONO, fontsize=size, color=color, fontweight=weight, zorder=9))
    fig.canvas.draw()
    r = fig.canvas.get_renderer(); inv = fig.transFigure.inverted()
    boxes = [inv.transform([(b.x0, b.y0), (b.x1, b.y1)]) for b in (t.get_window_extent(r) for t in drawn)]
    x0 = min(b[0][0] for b in boxes); y0 = min(b[0][1] for b in boxes)
    x1 = max(b[1][0] for b in boxes); y1 = max(b[1][1] for b in boxes)
    px = 0.0
    # the lockup must clear every bar beneath it
    to_fig = lambda xd, yd: inv.transform(ax.transData.transform((xd, yd)))
    for i in x:
        bx, by = to_fig(i, pos[i])
        if x0 - 0.01 < bx < x1 + 0.01 and by > y0 - 0.02:
            print(f"note: bar {i} (top y={by:.2f}) runs into the lockup (bottom y={y0:.2f})")
    if x1 + px > 0.82 or x0 - px < 0.18:
        print(f"note: text block spans x={x0 - px:.2f} to {x1 + px:.2f}, outside the 0.18-0.82 crop-safe band")
    fig.savefig(OUT, facecolor=SURFACE, dpi=DPI)
    print(f"wrote {OUT}; headline {-last:.1f}; commercial rank since war {n['commercial_rank_since_war']}")


if __name__ == "__main__":
    main()

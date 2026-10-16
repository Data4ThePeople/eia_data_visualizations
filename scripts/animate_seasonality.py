"""Animated GIFs of the diesel and gasoline seasonality charts for the oil-draw-update post.

Same look as petroleum_seasonality_v2_viz.html: one line per year on a week 1-52 axis,
prior years shaded by decade, 2026 in bold red, average and interquartile band of prior
years. Prior years rush by, then 2026 draws in one week at a time, and the finished chart
holds. The label on the 2026 line shows only real weekly values.

    python scripts/animate_seasonality.py [distillate|gasoline|total] [--static]

--static renders only the finished chart as a PNG (used for the email chart).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image
from weekly_draws import fetch

PRODUCTS = {  # column, file stem, title, series id, series description
    "distillate": ("02-diesel-seasonality", "U.S. Distillate Fuel Oil (Diesel): Weekly Seasonality", "WDISTUS1",
                   "distillate fuel oil"),
    "total": ("email-crude-seasonality", "U.S. Crude Oil (incl. SPR): Weekly Seasonality", "WCRSTUS1",
              "crude oil, including the SPR"),
    "gasoline": ("03-gasoline-seasonality", "U.S. Total Gasoline: Weekly Seasonality", "WGTSTUS1",
                 "total motor gasoline"),
}
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
STATIC = "--static" in sys.argv
PRODUCT = ARGS[0] if ARGS else "distillate"
STEM, TITLE, SERIES_ID, SERIES_DESC = PRODUCTS[PRODUCT]
OUT = f"posts/oil-draw-update/images/{STEM}.gif"
LAST_PNG = f"posts/oil-draw-update/images/{STEM}{'' if STATIC else '-final'}.png"
LOGO = os.path.expanduser("~/PycharmProjects/WarTaxViz/logos/d4tp-text-dark@2x.png")
CUR_RED = "#c0392b"
DECADES = {  # light (first year of decade) to dark (last), same values as the tool
    1980: ((110, 200, 225, .28), (0, 120, 150, .86)),
    1990: ((120, 200, 135, .28), (18, 122, 42, .86)),
    2000: ((118, 168, 228, .28), (10, 72, 172, .88)),
    2010: ((248, 178, 82, .28), (185, 85, 5, .88)),
    2020: ((200, 148, 228, .28), (108, 35, 162, .88)),
}
MID = {1980: (0, 140, 175), 1990: (18, 122, 42), 2000: (10, 72, 172), 2010: (185, 85, 5), 2020: (108, 35, 162)}
INK, INK2, GRID = "#1a1a1a", "#555550", "#e6e4dd"
DPI, W, H = 100, 10.6, 6.5
FRAME_MS = 80                  # GIF timing is in hundredths of a second, so 80 ms is exact
HOLD_S = 5.0


def shade(decade, frac):
    (lr, lg, lb, la), (dr, dg, db, da) = DECADES[decade]
    return ((lr + frac * (dr - lr)) / 255, (lg + frac * (dg - lg)) / 255, (lb + frac * (db - lb)) / 255,
            la + frac * (da - la))


def years(s):
    df = s.dropna().to_frame("v")
    doy = df.index.dayofyear
    df["year"], df["week"] = df.index.year, np.minimum((doy - 1) // 7 + 1, 52)
    return {y: (g.week.to_numpy(), g.v.to_numpy() / 1000) for y, g in df.groupby("year")}


def avg_band(ys, cur):
    """Mean and 25th-75th percentile of prior years by week, as in the tool: duplicate weeks
    averaged within a year, interior gaps filled linearly, numpy linear quantiles."""
    per = {}
    for y, (wk, v) in ys.items():
        if y >= cur:
            continue
        s = pd.Series(v).groupby(wk).mean()
        s = s.reindex(range(s.index.min(), s.index.max() + 1)).interpolate()
        for w, x in s.items():
            per.setdefault(w, []).append(x)
    weeks = sorted(per)
    return (np.array(weeks), np.array([np.mean(per[w]) for w in weeks]),
            np.array([np.quantile(per[w], .25) for w in weeks]), np.array([np.quantile(per[w], .75) for w in weeks]))


def main():
    w = fetch()
    ys = years(w[PRODUCT])
    cur = max(ys)
    prior = [y for y in sorted(ys) if y < cur]
    by_dec = {}
    for y in prior:
        by_dec.setdefault(y // 10 * 10, []).append(y)
    color = {y: shade(y // 10 * 10, g.index(y) / max(len(g) - 1, 1)) for g in by_dec.values() for y in g}
    aw, am, alo, ahi = avg_band(ys, cur)
    cw, cv = ys[cur]
    last_date = w[PRODUCT].dropna().index[-1]

    # schedule: (years fully drawn, partial year, fraction, 2026 weeks shown, show average)
    frames = []
    for i, y in enumerate(prior):
        steps = 1 if y < 2000 else 2 if y < 2020 else 4   # faster early, slower near the present
        for k in range(1, steps + 1):
            frames.append((i, y, k / steps, 0, False, FRAME_MS))
    frames.append((len(prior), None, 1, 0, True, 1200))   # average fades in, pause
    for n in range(1, len(cw) + 1):
        frames.append((len(prior), None, 1, n, True, 240 if n < len(cw) - 4 else 400))
    frames[-1] = frames[-1][:5] + (int(HOLD_S * 1000),)
    if STATIC:
        frames = frames[-1:]

    ymin = min(v.min() for _, v in ys.values()); ymax = max(v.max() for _, v in ys.values())
    # brand file is white on black; flatten on white and invert for a white background
    lg = Image.open(LOGO).convert("RGBA"); base = Image.new("RGBA", lg.size, (255, 255, 255, 255)); base.alpha_composite(lg)
    logo = np.asarray(Image.eval(base.convert("RGB"), lambda v: 255 - v))
    imgs, durs = [], []
    for done, part, frac, n_cur, show_avg, dur in frames:
        fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="white")
        ax = fig.add_axes([0.075, 0.17, 0.9, 0.62])
        ax.set_facecolor("white")
        for sp in ["top", "right"]:
            ax.spines[sp].set_visible(False)
        for sp in ["left", "bottom"]:
            ax.spines[sp].set_color("#cfcdc5")
        ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
        ax.set_xlim(0.5, 52.5); ax.set_ylim(np.floor(ymin / 10) * 10 - 5, np.ceil(ymax / 10) * 10 + 5)
        ax.set_xticks(range(1, 53, 2)); ax.tick_params(colors=INK2, labelsize=9, length=0)
        ax.set_xlabel("Week of year", color=INK2, fontsize=11, fontweight="bold", labelpad=8)
        ax.set_ylabel("Million barrels", color=INK2, fontsize=11, fontweight="bold")
        if show_avg:
            ax.fill_between(aw, alo, ahi, color=(0.5, 0.5, 0.5, 0.18), lw=0, zorder=1)
            ax.plot(aw, am, color=(0.07, 0.07, 0.07, 0.95), lw=2.2, ls=(0, (3, 2)), zorder=2)
        for y in prior[:done]:
            wk, v = ys[y]; ax.plot(wk, v, color=color[y], lw=1, zorder=3)
        banner_year, banner_col = None, INK2
        if part is not None:
            wk, v = ys[part]; m = max(2, int(round(len(wk) * frac)))
            lw = 1 if frac >= 1 else 1.6
            ax.plot(wk[:m], v[:m], color=color[part][:3] + (1,) if frac < 1 else color[part], lw=lw, zorder=4)
            banner_year, banner_col = part, tuple(c / 255 for c in MID[part // 10 * 10])
        if n_cur:
            ax.plot(cw[:n_cur], cv[:n_cur], color=CUR_RED, lw=3, zorder=6, solid_capstyle="round")
            ax.plot(cw[n_cur - 1], cv[n_cur - 1], "o", ms=7, color=CUR_RED, mec="white", mew=1.5, zorder=7)
            ax.annotate(f"{cv[n_cur - 1]:.1f}", (cw[n_cur - 1], cv[n_cur - 1]), xytext=(9, -2),
                        textcoords="offset points", color=CUR_RED, fontsize=11, fontweight="bold", va="center", zorder=8,
                        bbox=dict(facecolor="white", edgecolor="none", pad=1, alpha=0.85))
            banner_year, banner_col = cur, CUR_RED
        if banner_year:
            fig.text(0.975, 0.955, str(banner_year), ha="right", va="top",
                    color=banner_col, fontsize=34, fontweight="bold", alpha=0.9, zorder=9)
        fig.text(0.025, 0.955, TITLE, color=INK, fontsize=17,
                 fontweight="bold", va="top")
        fig.text(0.025, 0.905, f"Ending stocks by week of year (1 to 52), one line per year, {prior[0]} to {cur}. "
                 f"{cur} in bold red.", color=INK2, fontsize=10.5, va="top")
        handles = [Line2D([], [], color=CUR_RED, lw=3, label=str(cur)),
                   (Patch(color=(0.5, 0.5, 0.5, 0.25)), Line2D([], [], color=INK, lw=2, ls=(0, (3, 2))))]
        labels = [str(cur), "Average + IQR (prior years)"]
        for d in sorted(by_dec, reverse=True):  # only decades with data
            handles.append(Line2D([], [], color=tuple(c / 255 for c in MID[d]), lw=1.6)); labels.append(f"{d}s")
        from matplotlib.legend_handler import HandlerTuple
        fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.02, 0.875), ncol=7, frameon=False,
                   fontsize=10, labelcolor=INK2, handlelength=2.2, columnspacing=1.6,
                   handler_map={tuple: HandlerTuple(ndivide=1)})
        fig.text(0.025, 0.03, f"Source: EIA series {SERIES_ID}, weekly U.S. ending stocks of {SERIES_DESC}, "
                 f"thousand barrels (plotted in millions).\nData through the week ending "
                 f"{last_date:%B} {last_date.day}, {last_date.year}. Week = day of year / 7, capped at 52.",
                 color=INK2, fontsize=8.5, va="bottom")
        lax = fig.add_axes([0.80, 0.02, 0.175, 0.045]); lax.imshow(logo); lax.axis("off")
        fig.canvas.draw()
        im = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB")
        plt.close(fig)
        imgs.append(im); durs.append(dur)
    imgs[-1].save(LAST_PNG)
    if STATIC:
        print(f"static -> {LAST_PNG}")
        return
    # one shared palette from a strip of frames across the whole run, so every color used survives
    pick = imgs[:: max(1, len(imgs) // 12)] + [imgs[-1]]
    strip = Image.new("RGB", (imgs[0].width, imgs[0].height * len(pick)))
    for i, im in enumerate(pick):
        strip.paste(im, (0, i * imgs[0].height))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in imgs]
    q[0].save(OUT, save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True, disposal=1)
    print(f"{len(imgs)} frames, {sum(durs) / 1000:.1f} s, {os.path.getsize(OUT) / 1e6:.2f} MB -> {OUT}")
    print("2026 labels:", [f"{x:.1f}" for x in cv])


if __name__ == "__main__":
    main()

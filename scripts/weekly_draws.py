"""Weekly change in U.S. crude oil stocks since the war began, split into commercial
and Strategic Petroleum Reserve (SPR), plus the diesel figures quoted in the post.

Pulls EIA weekly stocks live, writes data/weekly_draws.csv, data/weekly_draws_numbers.json
and posts/oil-draw-update/images/01-weekly-crude-draws.png. Run from the repo root.
"""
import sys, os, json, datetime as dt
sys.path.insert(0, os.path.expanduser("~/.claude/d4tp-process"))
sys.path.insert(0, os.path.dirname(__file__))
from d4tp_env import load_env, get_key
import requests, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from plot_style import *

WAR_START = "2026-02-28"   # conflict begins; date as used in the SPR_explainer and Sulfur posts
SERIES = {"WCRSTUS1": "total", "WCESTUS1": "commercial", "WCSSTUS1": "spr", "WDISTUS1": "distillate", "WGTSTUS1": "gasoline"}
OUT_PNG = "posts/oil-draw-update/images/01-weekly-crude-draws.png"
COMM, SPR = "#3987e5", "#c98500"   # house blue and yellow, validated together on #181A1B


def fetch():
    """One series per request, paged by offset. Sorting by period alone is not a stable order
    across pages when several series share a period, which repeats some rows."""
    load_env()
    rows = []
    for sid in SERIES:
        p = {"api_key": get_key("EIA_API_KEY"), "frequency": "weekly", "data[0]": "value", "facets[series][0]": sid,
             "start": "1982-01-01", "length": 5000, "sort[0][column]": "period", "sort[0][direction]": "asc"}
        off = 0
        while True:
            p["offset"] = off
            for t in range(4):
                try:
                    j = requests.get("https://api.eia.gov/v2/petroleum/stoc/wstk/data/", params=p, timeout=90).json()["response"]
                    break
                except Exception:
                    if t == 3:
                        raise
            rows += j["data"]
            off += 5000
            if off >= int(j["total"]):
                break
    df = pd.DataFrame(rows)
    if df.duplicated(["period", "series"]).any():
        raise SystemExit("duplicate period/series rows from EIA")
    df["value"] = df["value"].astype(float)
    w = df.pivot(index="period", columns="series", values="value").rename(columns=SERIES).sort_index()
    w.index = pd.to_datetime(w.index)
    return w


def numbers(w):
    d = w.diff()
    war = d[d.index > WAR_START]                  # weeks ending after Feb 28 include war days
    last = d.index[-1]
    n = {"latest_week": str(last.date())}
    for c in ["total", "commercial", "spr", "distillate"]:
        n[f"{c}_change"] = d[c].iloc[-1]
        n[f"{c}_level"] = w[c].iloc[-1]
    n["commercial_minus_spr_check"] = w.commercial.iloc[-1] + w.spr.iloc[-1] - w.total.iloc[-1]
    # rank of this week's draw among war weeks (1 = largest draw)
    n["total_rank_since_war"] = int((war.total < d.total.iloc[-1]).sum() + 1)
    n["commercial_rank_since_war"] = int((war.commercial < d.commercial.iloc[-1]).sum() + 1)
    n["war_weeks"] = len(war)
    big = war.total.idxmin()
    n["largest_total_draw_week"], n["largest_total_draw"] = str(big.date()), war.total.min()
    n["largest_total_draw_split"] = {"commercial": war.commercial[big], "spr": war.spr[big]}
    prev = d.total[(d.total <= d.total.iloc[-1]) & (d.index < last)]
    n["last_larger_total_draw"] = [str(prev.index[-1].date()), prev.iloc[-1]]
    prevc = d.commercial[(d.commercial <= d.commercial.iloc[-1]) & (d.index < last)]
    n["last_larger_commercial_draw"] = [str(prevc.index[-1].date()), prevc.iloc[-1]]
    n["largest_total_draw_spr_share_pct"] = 100 * war.spr[big] / war.total[big]
    nz = war.spr[(war.spr == 0)]
    n["war_weeks_spr_unchanged"] = [str(x.date()) for x in nz.index]
    spr_draws = war.spr[war.spr < 0]
    n["spr_first_draw_week"] = str(spr_draws.index[0].date())
    n["cum_change_since_war"] = {c: w[c].iloc[-1] - w[c][w.index <= WAR_START].iloc[-1] for c in ["total", "commercial", "spr"]}
    n["cum_spr_share_pct"] = 100 * n["cum_change_since_war"]["spr"] / n["cum_change_since_war"]["total"]
    n["distillate_at_aug23_post"] = [str(w.distillate.loc[:"2026-08-19"].index[-1].date()), w.distillate.loc[:"2026-08-19"].iloc[-1]]  # latest week published before the Aug 23 diesel post
    # diesel: same week of year, nearest date to the latest week in every year
    doy = last.dayofyear
    same = w.distillate.groupby(w.index.year).apply(lambda s: s.iloc[(s.index.dayofyear - doy).to_series().abs().argmin()]
                                                    if (abs(s.index.dayofyear - doy) <= 3).any() else None).dropna()
    n["distillate_same_week_rank_low"] = int((same < w.distillate.iloc[-1]).sum() + 1)
    n["distillate_same_week_years"] = len(same)
    n["distillate_same_week_next_lowest"] = [int(same.drop(last.year).idxmin()), same.drop(last.year).min()]
    avg5 = same.loc[last.year - 5:last.year - 1]
    n["distillate_5yr_avg"], n["distillate_vs_5yr_pct"] = avg5.mean(), 100 * (w.distillate.iloc[-1] / avg5.mean() - 1)
    n["distillate_change_pct"] = 100 * d.distillate.iloc[-1] / w.distillate.iloc[-2]
    n["distillate_rank_draw_since_war"] = int((war.distillate < d.distillate.iloc[-1]).sum() + 1)
    lowsince = w.distillate[(w.distillate <= w.distillate.iloc[-1]) & (w.index < last)]
    n["distillate_last_lower"] = [str(lowsince.index[-1].date()), lowsince.iloc[-1]]
    # gasoline (series starts 1990), same same-week method as diesel
    g = w.gasoline.dropna(); gd = g.diff(); gwar = gd[gd.index > WAR_START]
    gsame = g.groupby(g.index.year).apply(lambda s: s.iloc[(s.index.dayofyear - doy).to_series().abs().argmin()]
                                          if (abs(s.index.dayofyear - doy) <= 3).any() else None).dropna()
    n["gasoline_change"], n["gasoline_level"] = gd.iloc[-1], g.iloc[-1]
    n["gasoline_change_pct"] = 100 * gd.iloc[-1] / g.iloc[-2]
    n["gasoline_build_rank_since_war"] = int((gwar > gd.iloc[-1]).sum() + 1)
    n["gasoline_same_week_years"], n["gasoline_same_week_years_lower"] = len(gsame), int((gsame < g.iloc[-1]).sum())
    ga5 = gsame.loc[last.year - 5:last.year - 1]
    n["gasoline_5yr_avg"], n["gasoline_vs_5yr_pct"] = ga5.mean(), 100 * (g.iloc[-1] / ga5.mean() - 1)
    n["gasoline_cum_change_since_war"] = g.iloc[-1] - g[g.index <= WAR_START].iloc[-1]
    return d, n


def chart(d, n, out=OUT_PNG, size=(11, 6.6), upto=None):
    """upto=k draws only the first k war weeks inside the finished chart's frame (for the
    social animation); out=None returns the figure instead of saving it."""
    use_house_style()
    full = d[d.index > WAR_START] / 1000
    k = len(full) if upto is None else upto
    final = k == len(full)
    war = full.iloc[:k]
    x = war.index
    fig, ax = plt.subplots(figsize=size)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.965 - 1.3 / size[1], bottom=0.14)
    width = 5.2
    pos_base = pd.Series(0.0, index=x); neg_base = pd.Series(0.0, index=x)
    for col, color in [("commercial", COMM), ("spr", SPR)]:
        v = war[col]
        base = neg_base.where(v < 0, pos_base)
        ax.bar(x, v, width=width, bottom=base, color=color, edgecolor=SURFACE, linewidth=1.2, zorder=3)
        neg_base += v.clip(upper=0); pos_base += v.clip(lower=0)
    ax.scatter(x, war.total, marker="_", s=90, color=INK, linewidths=2, zorder=4)
    ax.axhline(0, color=INK_DIM, lw=0.9, zorder=2)
    ax.yaxis.grid(True, zorder=0)
    ax.set_ylabel("Million barrels, change from prior week", color=INK_DIM, fontsize=10)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    AP = {3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "Aug.", 9: "Sept.", 10: "Oct."}
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: AP.get(mdates.num2date(v).month, mdates.num2date(v).strftime("%b."))))
    ax.set_xlim(full.index[0] - pd.Timedelta(days=6), full.index[-1] + pd.Timedelta(days=6))
    big = pd.Timestamp(n["largest_total_draw_week"])
    if big <= x[-1]:
        ax.annotate(f'Largest: {-n["largest_total_draw"]/1000:.1f} million\nweek ending May 15',
                    (big, n["largest_total_draw"] / 1000), xytext=(-16, 0), textcoords="offset points",
                    ha="right", va="center", color=INK_DIM, fontsize=9.5, linespacing=1.3)
    last = full.index[-1]
    if final:
        # call out the latest week: an outline around its bar
        ax.add_patch(plt.Rectangle((last - pd.Timedelta(days=4.6), n["total_change"] / 1000 - 0.9),
                                   pd.Timedelta(days=9.2), -n["total_change"] / 1000 + 1.8, fill=False,
                                   edgecolor=INK, lw=1.6, joinstyle="round", zorder=5))
        ax.annotate(f'Oct. 9: {-n["total_change"]/1000:.1f} million,\nall commercial',
                    (last, n["total_change"] / 1000), xytext=(-22, -4), textcoords="offset points",
                    ha="right", va="top", color=INK, fontsize=10, fontweight="bold", linespacing=1.3)
    ax.set_ylim(min(-21, full.total.min() - 4), max(full[["commercial"]].max().max(), 8) + 3)
    if not final:   # running date while the bars draw in; a real week-ending date, nothing interpolated
        ax.text(0.985, 0.95, f"Week ending {x[-1]:%B} {x[-1].day}", transform=ax.transAxes, ha="right", va="top",
                color=INK_DIM, fontsize=13, fontweight="bold")
    titleblock(fig, "Weekly change in U.S. crude oil stocks since the war began",
               "Bars split each week into commercial stocks and the Strategic Petroleum Reserve. "
               "The white tick is the total.\nWeeks ending March 6 to October 9, 2026.")
    x0, r = 0.03, fig.canvas.get_renderer()
    leg_y = 0.965 - 1.0 / fig.get_figheight()      # legend a fixed distance (inches) under the title
    for word, c in [("Commercial", COMM), ("Strategic Petroleum Reserve", SPR), ("Total", INK)]:
        t = fig.text(x0, leg_y, word, color=c, fontsize=11, fontweight="bold", va="center")
        x0 = fig.transFigure.inverted().transform(t.get_window_extent(r))[1][0] + 0.3 / fig.get_figwidth()
    credit(fig, "Source: U.S. Energy Information Administration, Weekly Petroleum Status Report "
                "\n(series WCESTUS1, WCSSTUS1, WCRSTUS1). Total is EIA's published crude total, commercial plus SPR.")
    if out is None:
        return fig
    fig.savefig(out)


if __name__ == "__main__":
    w = fetch()
    d, n = numbers(w)
    os.makedirs("data", exist_ok=True)
    pd.concat([w, d.add_suffix("_chg")], axis=1).loc["2025-12-01":].to_csv("data/weekly_draws.csv", float_format="%.0f")
    json.dump(n, open("data/weekly_draws_numbers.json", "w"), indent=1, default=float)
    chart(d, n)
    print(json.dumps(n, indent=1, default=float))

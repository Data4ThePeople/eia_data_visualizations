"""Animated GIF of the weekly crude draws chart for social posts.

The bars draw in one war week at a time over about 8 seconds, then the finished chart holds
for about 5. Every frame comes from chart() in weekly_draws.py, so the last frame is the
published chart (images/01-weekly-crude-draws.png); the running date shows real week-ending
dates only.

    python scripts/animate_draws.py [seconds] [hold_seconds]
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib.pyplot as plt
from PIL import Image
from weekly_draws import fetch, numbers, chart, WAR_START

OUT = "posts/oil-draw-update/social/weekly-crude-draws.gif"
SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
HOLD = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
SIZE = (11, 6.6)
DPI = 1200 / SIZE[0]          # 1200 px wide


def grab(fig):
    fig.set_dpi(DPI)
    fig.canvas.draw()
    im = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB").copy()
    plt.close(fig)
    return im


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    w = fetch()
    d, n = numbers(w)
    weeks = int((d.index > WAR_START).sum())
    frames = [grab(chart(d, n, out=None, size=SIZE, upto=k)) for k in range(1, weeks)]
    last = grab(chart(d, n, out=None, size=SIZE))
    step = int(round(SECONDS * 1000 / len(frames) / 10) * 10)     # GIF timing is in hundredths of a second
    pal = last.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames] + [pal]
    q[0].save(OUT, save_all=True, append_images=q[1:], duration=[step] * len(frames) + [int(HOLD * 1000)],
              loop=0, optimize=False, disposal=1)
    last.save(OUT.replace(".gif", "-final-frame.png"))
    print(f"{OUT}: {len(q)} frames, {last.size[0]}x{last.size[1]}, {step * len(frames) / 1000:.1f}s + {HOLD:.0f}s hold, "
          f"{os.path.getsize(OUT) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()

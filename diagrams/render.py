"""Regenerate the original diagrams. Optional dependencies: matplotlib and Pillow."""
from io import BytesIO
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyze import read_points, summarize

TARGET = (100, 50)


def panel(ax, points, title, legend=False):
    ax.set_title(title, loc="left", fontweight="bold", fontsize=18, pad=12)
    ax.set(xlim=(-2.8, 2.8), ylim=(-1.85, 1.85), aspect="equal",
           xlabel="X error (mm)", ylabel="Y error (mm)")
    ax.axvline(0, color="#92adbd", lw=1)
    ax.axhline(0, color="#92adbd", lw=1)
    ax.grid(color="#dbe8ef", lw=.8)
    ax.set_xticks([-2, -1, 0, 1, 2])
    ax.set_yticks([-1.5, -.75, 0, .75, 1.5])
    ax.tick_params(labelsize=13)
    ax.scatter([x - 100 for x, y in points], [y - 50 for x, y in points],
               s=94, color="#087b76", edgecolors="white", zorder=4, label="Reading")
    r = summarize(TARGET, points)
    ax.scatter(*r.offset, s=136, marker="o", facecolors="none", edgecolors="#9b360d",
               linewidth=2, zorder=5, label="Mean")
    ax.scatter(0, 0, s=75, marker="+", color="#172e49", zorder=6, label="Target")
    if legend:
        ax.legend(loc="upper left", ncols=3, fontsize=11, framealpha=.95)


def save(fig, filename):
    raw = BytesIO()
    fig.savefig(raw, format="png", dpi=120, facecolor="#f3f8fa")
    raw.seek(0)
    with Image.open(raw) as im:
        im.convert("RGB").save(ROOT / "diagrams" / filename, "WEBP", quality=87, method=6)
    plt.close(fig)


def samples(name):
    return read_points(ROOT / "examples" / f"{name}.csv")


def main():
    fig, axes = plt.subplots(2, 1, figsize=(7, 8.8), layout="constrained")
    panel(axes[0], samples("tight_offset"), "Tight cluster, 2 mm to the right", legend=True)
    panel(axes[1], samples("centered_wide"), "Centered cluster, wider spread")
    save(fig, "endpoint-clusters.webp")

    fig, ax = plt.subplots(figsize=(7, 4.6), layout="constrained")
    ax.set_title("Two approaches to one target", loc="left", fontweight="bold", fontsize=19)
    ax.axvline(0, color="#172e49", lw=2, label="Target and pooled mean")
    for y, name, color in [(1, "approach_positive", "#087b76"), (0, "approach_negative", "#9b360d")]:
        pts = samples(name)
        ax.scatter([x - 100 for x, _ in pts], [y] * len(pts), s=105,
                   c=color, edgecolors="white", zorder=3)
    ax.set(xlim=(-1.6, 1.6), ylim=(-.65, 1.65), xlabel="X error (mm)")
    ax.set_yticks([0, 1], ["Negative", "Positive"])
    ax.grid(axis="x", color="#dbe8ef", lw=1)
    ax.tick_params(labelsize=15)
    ax.legend(loc="lower right", fontsize=13)
    save(fig, "approach-groups.webp")


if __name__ == "__main__":
    main()

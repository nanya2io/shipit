"""
ShipIt.exe - Attention Lens (static report figure)
======================================================
Renders the same self-attention data shown in the interactive dashboard
as a static matplotlib heatmap grid, suitable for pasting into a Word
report (the interactive HTML heatmap can't be embedded in a .docx).

Reads outputs/attention_lens_data.json (produced by 04_attention_lens.py)
and produces one combined figure: one heatmap row per chapter, word
labels on the x-axis, attention intensity as color.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

IN_PATH = "outputs/attention_lens_data.json"
OUT_PATH = "outputs/attention_heatmap_report.png"

# Y2K-consistent colormap: near-black -> purple -> hot pink -> cyan
Y2K_CMAP = LinearSegmentedColormap.from_list(
    "y2k_attention", ["#0a0014", "#7B2FF7", "#FF2E9A", "#00E5FF"]
)

CHAPTER_LABELS = {
    "the_spark": "Ch.1 — The Spark",
    "the_shift": "Ch.2 — The Shift",
    "the_turn": "Ch.3 — The Turn",
    "the_resolution": "Ch.4 — The Resolution",
}


def wrap_tokens(tokens, max_per_row=10):
    """Split a long token list into rows so labels stay readable."""
    return [tokens[i:i+max_per_row] for i in range(0, len(tokens), max_per_row)]


def plot_chapter_heatmap(ax, chapter_key, data):
    tokens = [t["token"] for t in data["tokens"]]
    weights = [t["attention"] for t in data["tokens"]]

    matrix = np.array(weights).reshape(1, -1)
    im = ax.imshow(matrix, cmap=Y2K_CMAP, aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(tokens)))
    ax.set_xticklabels(tokens, rotation=40, ha="right", fontsize=9, color="#222")
    ax.set_yticks([])
    ax.set_title(CHAPTER_LABELS.get(chapter_key, chapter_key), fontsize=11,
                 fontweight="bold", color="#7B2FF7", loc="left", pad=8)

    for spine in ax.spines.values():
        spine.set_visible(False)

    return im


def main():
    with open(IN_PATH, encoding="utf-8") as f:
        attn_data = json.load(f)

    chapter_order = ["the_spark", "the_shift", "the_turn", "the_resolution"]
    fig, axes = plt.subplots(len(chapter_order), 1, figsize=(9, 9.2))
    fig.suptitle(
        "Attention Lens: Self-Attention Weights per Chapter's Key Sentence\n"
        "(GPT-2, final layer, averaged across heads — brighter = higher attention weight)",
        fontsize=11, fontweight="bold", y=0.99
    )

    im = None
    for ax, key in zip(axes, chapter_order):
        if key in attn_data:
            im = plot_chapter_heatmap(ax, key, attn_data[key])

    fig.tight_layout(rect=[0, 0.07, 1, 0.94])
    if im is not None:
        cbar_ax = fig.add_axes([0.25, 0.025, 0.5, 0.018])
        fig.colorbar(im, cax=cbar_ax, orientation="horizontal", label="Attention weight (0-1)")

    fig.savefig(OUT_PATH, dpi=170, facecolor="white")
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

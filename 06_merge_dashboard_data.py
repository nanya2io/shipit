"""
LoreX - Merge Pipeline Outputs
=======================================
Combines the outputs of stages 01-04 into the single JSON structure
dashboard.html expects. Run this after generating a new story so you
can rebuild the dashboard with your own live data instead of the demo.

Usage:
    python 06_merge_dashboard_data.py \
        --classified data/story_classified.json \
        --brainrot data/story_brainrot.json \
        --attention data/attention_lens_data.json \
        --out outputs/dashboard_data.json

--brainrot and --attention are optional -- omit either if you haven't
run those stages yet; the dashboard will just show fewer panels.
"""
import argparse
import json
import os

TAXONOMY_PATH = "data/trope_taxonomy.json"


def build_structural_summary(story):
    summary = {}
    for ch in story["chapters"]:
        role = ch["structural_role"]
        summary[role] = [t["trope_name"] for t in ch.get("detected_tropes", [])]
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--classified", required=True,
                         help="Output of 02_classify_tropes.py")
    parser.add_argument("--brainrot", default=None,
                         help="Output of 03_brainrot_mode.py (optional)")
    parser.add_argument("--attention", default=None,
                         help="Output of 04_attention_lens.py, one file per sentence "
                              "merged into a dict keyed by chapter id (optional)")
    parser.add_argument("--out", default="outputs/dashboard_data.json")
    args = parser.parse_args()

    with open(args.classified, encoding="utf-8") as f:
        story = json.load(f)

    with open(TAXONOMY_PATH, encoding="utf-8") as f:
        taxonomy = json.load(f)["tropes"]

    if args.brainrot:
        with open(args.brainrot, encoding="utf-8") as f:
            brainrot_story = json.load(f)
        brainrot_by_chapter = {
            ch["chapter_number"]: ch.get("brainrot_text", "")
            for ch in brainrot_story["chapters"]
        }
        for ch in story["chapters"]:
            ch["brainrot_text"] = brainrot_by_chapter.get(ch["chapter_number"], "")

    if args.attention:
        with open(args.attention, encoding="utf-8") as f:
            attn_data = json.load(f)
        for ch in story["chapters"]:
            if ch["id"] in attn_data:
                ch["attention_lens"] = {
                    "sentence": attn_data[ch["id"]]["sentence"],
                    "tokens": attn_data[ch["id"]]["tokens"],
                }

    output = {
        "meta": {
            "note": "Generated via the full LoreX pipeline.",
            "attention_note": (
                "Attention weights from GPT-2's self-attention (final layer, "
                "averaged across heads, attention from the final token to each "
                "earlier token)." if args.attention else ""
            ),
        },
        "taxonomy": taxonomy,
        "story": story,
        "structural_summary": build_structural_summary(story),
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Merged dashboard data written to {args.out}")
    print(f"  Chapters: {len(story['chapters'])}")
    print(f"  Brainrot mode: {'yes' if args.brainrot else 'no'}")
    print(f"  Attention lens: {'yes' if args.attention else 'no'}")
    print("\nNext: python build_dashboard.py  (regenerates dashboard.html from this file)")


if __name__ == "__main__":
    main()

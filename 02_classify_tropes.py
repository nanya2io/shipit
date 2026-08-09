"""
ShipIt.exe - Trope Classification Engine
============================================
Scores each generated chapter against the curated trope taxonomy and
extracts the exact sentence(s) that triggered each detection, so every
score is explainable rather than a black-box number.

Two scoring modes, combined:
  1. Keyword/marker overlap (runs anywhere, no downloads needed)
  2. Semantic similarity via Sentence-Transformers, if available
     (stronger signal, catches paraphrased tropes the keyword list
     misses -- requires all-MiniLM-L6-v2 from Hugging Face)

This script runs fully offline in keyword-only mode, which is what
makes it possible to validate classification quality on real text
even in network-restricted environments.
"""
import json
import re
import argparse

TAXONOMY_PATH = "data/trope_taxonomy.json"

try:
    import nltk
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer, util
    _EMBEDDER = None  # lazy-loaded
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


def load_taxonomy():
    with open(TAXONOMY_PATH, encoding="utf-8") as f:
        return json.load(f)["tropes"]


def split_sentences(text):
    text = text.strip()
    if NLTK_AVAILABLE:
        return [s.strip() for s in sent_tokenize(text) if s.strip()]
    # fallback: naive split, only used if nltk truly unavailable
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def keyword_score(sentence, trope):
    sentence_lower = sentence.lower()
    hits = []
    for marker in trope["markers"]:
        pattern = r'\b' + re.escape(marker.lower()) + r'\b'
        if re.search(pattern, sentence_lower):
            hits.append(marker)
    return len(hits), hits


def get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBEDDER


def classify_chapter(chapter_text, taxonomy, use_embeddings=False, threshold=0.42):
    sentences = split_sentences(chapter_text)
    results = []

    embedder = get_embedder() if (use_embeddings and EMBEDDINGS_AVAILABLE) else None
    sentence_embeds = embedder.encode(sentences, convert_to_tensor=True) if embedder else None

    for trope in taxonomy:
        evidence = []
        keyword_hits_total = 0

        for i, sent in enumerate(sentences):
            n_hits, hits = keyword_score(sent, trope)
            keyword_hits_total += n_hits
            if n_hits > 0:
                evidence.append({"sentence": sent, "matched_markers": hits, "method": "keyword"})

        semantic_score = 0.0
        if embedder is not None:
            trope_embed = embedder.encode(trope["definition"], convert_to_tensor=True)
            sims = util.cos_sim(trope_embed, sentence_embeds)[0]
            best_idx = int(sims.argmax())
            semantic_score = float(sims[best_idx])
            if semantic_score >= threshold and not any(
                e["sentence"] == sentences[best_idx] for e in evidence
            ):
                evidence.append({
                    "sentence": sentences[best_idx],
                    "matched_markers": [],
                    "method": "semantic",
                    "similarity": round(semantic_score, 3),
                })

        # combined score: keyword hits are a strong direct signal;
        # semantic similarity adds recall for paraphrased tropes
        combined_score = min(1.0, (keyword_hits_total * 0.22) + (semantic_score if embedder else 0))

        if evidence:
            results.append({
                "trope_id": trope["id"],
                "trope_name": trope["name"],
                "score": round(combined_score, 3),
                "evidence": evidence[:3],  # cap for readability
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def classify_story(story, taxonomy, use_embeddings=False):
    classified = {"char_a": story["char_a"], "char_b": story["char_b"], "chapters": []}
    for chapter in story["chapters"]:
        tropes = classify_chapter(chapter["text"], taxonomy, use_embeddings=use_embeddings)
        classified["chapters"].append({
            **chapter,
            "detected_tropes": tropes,
            "top_trope": tropes[0]["trope_name"] if tropes else None,
        })
    return classified


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", default="data/story_output.json")
    parser.add_argument("--out", default="data/story_classified.json")
    parser.add_argument("--use-embeddings", action="store_true",
                         help="Also use Sentence-Transformers semantic similarity (needs Hugging Face access).")
    args = parser.parse_args()

    taxonomy = load_taxonomy()
    with open(args.story, encoding="utf-8") as f:
        story = json.load(f)

    if args.use_embeddings and not EMBEDDINGS_AVAILABLE:
        print("sentence-transformers not installed -- falling back to keyword-only mode.")
        args.use_embeddings = False

    classified = classify_story(story, taxonomy, use_embeddings=args.use_embeddings)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(classified, f, indent=2)

    print(f"\nClassified {len(classified['chapters'])} chapters "
          f"({'keyword + semantic' if args.use_embeddings else 'keyword-only'} mode)")
    for ch in classified["chapters"]:
        top3 = ", ".join(f"{t['trope_name']} ({t['score']})" for t in ch["detected_tropes"][:3])
        print(f"  Ch.{ch['chapter_number']} [{ch['structural_role']}]: {top3 or 'no strong matches'}")
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()

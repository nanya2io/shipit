"""
ShipIt.exe - Attention Lens
==============================
Extracts real self-attention weights from GPT-2 for a given sentence and
surfaces which words the model "looked at" most heavily -- a second,
mechanism-level layer of explainability that sits alongside the existing
evidence-quote system (which shows WHAT text triggered a trope; this
shows HOW the model internally weighted that text).

Concept
-------
Self-attention lets every token look at every earlier token and learn how
much to "weight" each one when building its own representation. In GPT-2
(a causal/decoder-only transformer), the LAST token in a sequence has
attended to the entire sentence -- so the attention FROM the last token
TO every earlier token is a reasonable, standard proxy for "which words
mattered most to the sentence's overall meaning as the model processed it."

This script:
  1. Tokenizes a sentence
  2. Runs it through GPT-2 with output_attentions=True
  3. Averages attention weights across all heads in the final layer
  4. Extracts the attention distribution FROM the last token TO all tokens
  5. Normalizes to produce a 0-1 "attention intensity" per word, ready
     for a heatmap

Run modes
---------
Auto mode (--story): the recommended way to run this. Reads a classified
story JSON (output of 02_classify_tropes.py) and automatically picks each
chapter's top-scoring trope's first evidence sentence -- no manual sentence
selection needed. Outputs a single file keyed by chapter id, ready to pass
straight to 06_merge_dashboard_data.py --attention.

    python 04_attention_lens.py --story data/story_classified.json --out data/attention_lens_data.json

Manual mode (--sentence): run on one specific sentence you choose yourself.

    python 04_attention_lens.py --sentence "Wren swore and finally turned around." --out data/attn_single.json

Both modes support --smoke-test: tiny randomly-initialized GPT-2 architecture,
whitespace tokenization instead of the real BPE tokenizer (which also
needs a Hugging Face download), purely to validate the extraction and
normalization pipeline offline. Produces placeholder attention patterns,
NOT a real trained model's attention.

    python 04_attention_lens.py --story data/story_classified.json --smoke-test
"""
import argparse
import json
import torch
from transformers import GPT2Config, GPT2Model, GPT2Tokenizer

SEED = 42


def load_model_real():
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2Model.from_pretrained("gpt2", output_attentions=True, attn_implementation="eager")
    model.eval()
    return tokenizer, model


class WhitespaceTokenizer:
    """Minimal stand-in for GPT2Tokenizer, used only in smoke-test mode
    since the real BPE tokenizer also requires a Hugging Face download."""
    def __init__(self):
        self.vocab = {}

    def tokenize_words(self, text):
        return text.strip().split()

    def encode_for_model(self, words, vocab_size=50257):
        torch.manual_seed(SEED)
        # deterministic-ish pseudo-ids per word (stable within a run)
        ids = [abs(hash(w)) % vocab_size for w in words]
        return torch.tensor([ids])


def load_model_smoke():
    print("[smoke-test] Using tiny randomly-initialized GPT-2 architecture "
          "(no download) with whitespace tokenization to validate the "
          "attention-extraction pipeline offline.")
    cfg = GPT2Config(n_layer=2, n_head=2, n_embd=64, vocab_size=50257,
                      output_attentions=True, attn_implementation="eager")
    model = GPT2Model(cfg)
    model.eval()
    tokenizer = WhitespaceTokenizer()
    return tokenizer, model


def extract_attention_real(sentence, tokenizer, model):
    inputs = tokenizer(sentence, return_tensors="pt")
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    with torch.no_grad():
        out = model(**inputs)
    # out.attentions: tuple of (n_layers) tensors, each [batch, heads, seq, seq]
    last_layer_attn = out.attentions[-1][0]          # [heads, seq, seq]
    avg_heads = last_layer_attn.mean(dim=0)           # [seq, seq]
    last_token_attn = avg_heads[-1]                   # [seq] -- what the last token attended to
    weights = last_token_attn.tolist()
    # clean up GPT-2's byte-level BPE markers for readability
    clean_tokens = [t.replace("Ġ", "").replace("Ċ", "\\n") or t for t in tokens]
    return clean_tokens, weights


def extract_attention_smoke(sentence, tokenizer, model):
    words = tokenizer.tokenize_words(sentence)
    ids = tokenizer.encode_for_model(words)
    with torch.no_grad():
        out = model(input_ids=ids)
    last_layer_attn = out.attentions[-1][0]
    avg_heads = last_layer_attn.mean(dim=0)
    last_token_attn = avg_heads[-1]
    weights = last_token_attn.tolist()
    return words, weights


def normalize_weights(weights):
    lo, hi = min(weights), max(weights)
    if hi - lo < 1e-9:
        return [0.5 for _ in weights]
    return [(w - lo) / (hi - lo) for w in weights]


def attention_lens(sentence, smoke_test=False):
    if smoke_test:
        tokenizer, model = load_model_smoke()
        tokens, weights = extract_attention_smoke(sentence, tokenizer, model)
    else:
        tokenizer, model = load_model_real()
        tokens, weights = extract_attention_real(sentence, tokenizer, model)

    norm_weights = normalize_weights(weights)
    result = [{"token": t, "attention": round(w, 4)} for t, w in zip(tokens, norm_weights)]
    return result


def select_evidence_sentence(chapter):
    """Auto-pick the sentence to run Attention Lens on: the top-scoring
    trope's first piece of evidence for this chapter. Returns None if the
    chapter has no detected tropes (e.g. keyword-only mode found nothing)."""
    tropes = chapter.get("detected_tropes", [])
    if not tropes:
        return None
    top_trope = tropes[0]
    evidence = top_trope.get("evidence", [])
    if not evidence:
        return None
    return evidence[0]["sentence"], top_trope["trope_name"]


def run_from_story(story_path, smoke_test=False):
    """Auto mode: for every chapter in a classified story, run Attention
    Lens on the top trope's evidence sentence. This is what
    06_merge_dashboard_data.py's --attention flag expects as input --
    no manual sentence-picking required."""
    with open(story_path, encoding="utf-8") as f:
        story = json.load(f)

    results = {}
    for chapter in story["chapters"]:
        picked = select_evidence_sentence(chapter)
        if picked is None:
            print(f"  Ch.{chapter['chapter_number']} ({chapter['title']}): "
                  f"no detected tropes with evidence -- skipping")
            continue
        sentence, trope_name = picked
        print(f"  Ch.{chapter['chapter_number']} ({chapter['title']}): "
              f"using top trope '{trope_name}' evidence -- \"{sentence[:60]}...\"")
        tokens = attention_lens(sentence, smoke_test=smoke_test)
        results[chapter["id"]] = {
            "sentence": sentence,
            "tokens": tokens,
            "source_trope": trope_name,
            "chapter_number": chapter["chapter_number"],
        }
    return results


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sentence", help="Run on a single, manually chosen sentence.")
    mode.add_argument("--story", help="Auto mode: pick each chapter's top-trope evidence "
                                       "sentence from a classified story JSON (output of "
                                       "02_classify_tropes.py) and run all of them.")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--out", default="data/attention_output.json")
    args = parser.parse_args()

    if args.story:
        print(f"Auto-selecting evidence sentences from {args.story} "
              f"({'SMOKE TEST' if args.smoke_test else 'LIVE'})")
        results = run_from_story(args.story, smoke_test=args.smoke_test)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved {len(results)} chapters' attention data to {args.out}")
        print("This file is ready to pass directly to "
              "06_merge_dashboard_data.py --attention")
    else:
        result = attention_lens(args.sentence, smoke_test=args.smoke_test)
        print(f"\nSentence: {args.sentence}")
        print(f"{'Token':<20} {'Attention':<10} {'Bar'}")
        for r in result:
            bar = "█" * int(r["attention"] * 30)
            print(f"{r['token']:<20} {r['attention']:<10} {bar}")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"sentence": args.sentence, "tokens": result, "smoke_test": args.smoke_test}, f, indent=2)
        print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()

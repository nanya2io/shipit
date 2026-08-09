"""
ShipIt.exe - Brainrot Mode
=============================
Takes a generated chapter and rewrites it in current internet-slang
register, WITHOUT changing the underlying plot events or character
actions -- this is a style-transfer task, not a rewrite task.

Deliberately does NOT hardcode specific memes/slang terms into the
prompt. Slang dates within weeks; hardcoding it guarantees the output
looks stale by the time anyone sees it. Instead, the model is asked to
draw on whatever slang it already knows is current, which ages far
better than anything scripted here would.

Run modes mirror 01_generate_story.py: live (needs GROQ_API_KEY) or
--smoke-test (validates pipeline wiring only).
"""
import argparse
import json
import os
import time

try:
    import requests
except ImportError:
    requests = None

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

BRAINROT_SYSTEM_PROMPT = (
    "You are rewriting a short story chapter in a chaotic, funny, current "
    "internet-slang register (the kind of voice used in Gen Z social media "
    "narration/commentary). Keep every plot event, character action, and "
    "emotional beat from the original EXACTLY the same -- you are changing "
    "the voice and register only, not the events. Feel free to use current "
    "internet slang, exaggerated reactions, and comedic asides, but the "
    "reader should still be able to follow the same story. Do not explain "
    "what you're doing -- output only the rewritten chapter."
)


def call_llm(messages, api_key, temperature=1.0, max_tokens=600, max_retries=5):
    if requests is None:
        raise RuntimeError("The 'requests' package is required for live generation.")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for attempt in range(max_retries):
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)

        if resp.status_code == 429:
            # Mirrors the retry/backoff in 01_generate_story.py so brainrot
            # rewrites (which fire right after story generation, same minute,
            # same rate limit) don't blow up on the first 429 they see.
            retry_after = resp.headers.get("Retry-After")
            wait_s = float(retry_after) if retry_after else (2 ** attempt) * 2
            wait_s = min(wait_s, 60) + 0.5
            print(f"    Rate limited (429) -- waiting {wait_s:.1f}s before retry "
                  f"{attempt + 1}/{max_retries}...")
            time.sleep(wait_s)
            continue

        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    raise RuntimeError(
        f"Still rate-limited after {max_retries} retries. Groq's free tier caps "
        f"requests/tokens per minute -- wait a minute and try again."
    )


def brainrot_rewrite_smoke(chapter_text, chapter_title):
    return (
        f"[SMOKE-TEST PLACEHOLDER — Brainrot rewrite of '{chapter_title}'] "
        f"Real slang rewrite is generated live when GROQ_API_KEY is set. "
        f"This placeholder exists only to validate the pipeline runs end to end."
    )


def brainrot_rewrite(chapter_text, chapter_title, api_key=None, smoke_test=False):
    if smoke_test:
        return brainrot_rewrite_smoke(chapter_text, chapter_title)
    messages = [
        {"role": "system", "content": BRAINROT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Original chapter:\n\n{chapter_text}"},
    ]
    return call_llm(messages, api_key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", default="data/story_classified.json")
    parser.add_argument("--out", default="data/story_brainrot.json")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not args.smoke_test and not api_key:
        raise SystemExit("No GROQ_API_KEY set. Use --smoke-test to validate without one.")

    with open(args.story, encoding="utf-8") as f:
        story = json.load(f)

    for chapter in story["chapters"]:
        t0 = time.time()
        rewrite = brainrot_rewrite(
            chapter["text"], chapter["title"], api_key=api_key, smoke_test=args.smoke_test
        )
        chapter["brainrot_text"] = rewrite
        print(f"  {chapter['title']}: rewritten in {time.time()-t0:.1f}s")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2)
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()

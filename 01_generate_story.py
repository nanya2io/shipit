"""
LoreX - Story Generation Engine
=======================================
Generates a 4-chapter narrative between two user-specified fictional
characters, one chapter at a time, carrying prior chapters forward as
context so voice and continuity hold up across the arc.

CHAPTER_BEATS define the structural role of each chapter -- this
structure is what lets the trope-classification stage later ask
"does trope X concentrate in the chapter where we'd expect it?"

Run modes
---------
Normal (default): calls a hosted LLM via the Groq API (or any
OpenAI-compatible endpoint). Requires an API key.

    export GROQ_API_KEY="your-key-here"
    python 01_generate_story.py --char-a "Kai" --char-b "Ren"

Smoke test (--smoke-test): skips the API call and returns a fixed
placeholder per chapter, purely to validate the pipeline's control
flow (context-carrying, file I/O, chapter numbering) without needing
a key. Produces placeholder text, NOT real generated prose.

    python 01_generate_story.py --char-a "Kai" --char-b "Ren" --smoke-test
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
GROQ_MODEL = "llama-3.1-8b-instant"  # fast + free-tier friendly; swap for a larger model for higher quality

CHAPTER_BEATS = [
    {
        "id": "the_spark",
        "title": "The Spark",
        "role": "setup",
        "instruction": (
            "Write the opening chapter of a crossover story about how {char_a} and {char_b} "
            "-- who may be from entirely different fictional universes -- first collide or "
            "are thrown together. If they're from different franchises, commit to a concrete, "
            "specific reason their worlds intersect (do not hand-wave this); if they're from "
            "the same universe, ground the meeting in their established context. Establish "
            "their initial dynamic clearly (tension, rivalry, curiosity, wariness -- whatever "
            "fits who they actually are). Ground it in a concrete scene with sensory detail "
            "and dialogue. This is a platonic story -- team-up, rivalry, or found-family "
            "dynamics, not a romance. Do not resolve anything yet -- end on an open, "
            "forward-pulling note. Aim for 250-350 words."
        ),
    },
    {
        "id": "the_shift",
        "title": "The Shift",
        "role": "rising_tension",
        "instruction": (
            "Continue the story. Something now forces {char_a} and {char_b} into closer "
            "collaboration or conflict -- raise the stakes from where the last chapter left "
            "off. Deepen their dynamic through a specific interaction, not a summary. Show, "
            "don't tell, any shift in how they see each other -- growing respect, trust, or "
            "a truce. Keep it platonic: this is about partnership, rivalry, or loyalty, not "
            "romantic feeling. Aim for 250-350 words."
        ),
    },
    {
        "id": "the_turn",
        "title": "The Turn",
        "role": "turning_point",
        "instruction": (
            "Continue the story. Write the decisive moment that changes the relationship "
            "between {char_a} and {char_b} -- a confrontation, a sacrifice, a moment of real "
            "trust, or an act that can't be undone. This is the emotional turning point of "
            "the whole story. Make it specific and earned by what's already happened. Keep "
            "the bond platonic -- loyalty, respect, or found-family closeness, not romance. "
            "Aim for 250-350 words."
        ),
    },
    {
        "id": "the_resolution",
        "title": "The Resolution",
        "role": "resolution",
        "instruction": (
            "Write the final chapter. Show where {char_a} and {char_b} land -- as allies, "
            "found family, or something in between -- after everything that's happened. "
            "This doesn't have to be a tidy happy ending -- it should feel true to the arc "
            "so far. Give it a real closing image or line. Keep it platonic throughout. "
            "Aim for 250-350 words."
        ),
    },
]

SYSTEM_PROMPT = (
    "You are a skilled fiction writer specializing in character-driven short "
    "fiction and crossover storytelling. When given two characters, write them "
    "consistently with how they are widely known and portrayed -- their "
    "established personality, voice, values, and (if applicable) abilities. "
    "If either character is obscure or you are not confident how they are "
    "typically portrayed, favor a grounded, understated characterization over "
    "invented specifics you are not sure about, rather than confidently "
    "fabricating traits. Do not write romantic or sexual content of any kind "
    "-- this is strictly a platonic story about partnership, rivalry, "
    "mentorship, or found family. Write with concrete sensory detail and "
    "natural dialogue -- avoid generic phrasing, cliche metaphors, and "
    "summary-style narration. Stay strictly in-universe: do not break the "
    "fourth wall, do not add meta-commentary, do not use headers or bullet "
    "points. Output only the chapter's prose."
)


def call_llm(messages, api_key, temperature=0.9, max_tokens=600, max_retries=5):
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
            # Groq's free tier rate-limits per minute; back off and retry
            # rather than failing the whole story generation.
            retry_after = resp.headers.get("Retry-After")
            wait_s = float(retry_after) if retry_after else (2 ** attempt) * 2
            wait_s = min(wait_s, 60) + 0.5  # cap the wait, small buffer
            print(f"    Rate limited (429) -- waiting {wait_s:.1f}s before retry "
                  f"{attempt + 1}/{max_retries}...")
            time.sleep(wait_s)
            continue

        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    raise RuntimeError(
        f"Still rate-limited after {max_retries} retries. Groq's free tier caps "
        f"requests/tokens per minute -- wait a minute and rerun, or add a short "
        f"delay between chapters with --chapter-delay."
    )


def generate_chapter_smoke(beat, char_a, char_b, chapter_num):
    return (
        f"[SMOKE-TEST PLACEHOLDER — Chapter {chapter_num}: {beat['title']}] "
        f"{char_a} and {char_b} continue their story here. This chapter's structural "
        f"role is '{beat['role']}'. Real prose is generated when GROQ_API_KEY is set "
        f"and --smoke-test is omitted."
    )


def generate_story(char_a, char_b, api_key=None, smoke_test=False, chapter_delay=0):
    story = {"char_a": char_a, "char_b": char_b, "chapters": []}
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    for i, beat in enumerate(CHAPTER_BEATS, start=1):
        instruction = beat["instruction"].format(char_a=char_a, char_b=char_b)
        conversation.append({"role": "user", "content": instruction})

        t0 = time.time()
        if smoke_test:
            text = generate_chapter_smoke(beat, char_a, char_b, i)
        else:
            text = call_llm(conversation, api_key)
        elapsed = time.time() - t0

        conversation.append({"role": "assistant", "content": text})

        story["chapters"].append({
            "chapter_number": i,
            "id": beat["id"],
            "title": beat["title"],
            "structural_role": beat["role"],
            "text": text,
            "generation_time_sec": round(elapsed, 2),
        })
        print(f"  Chapter {i} ({beat['title']}): {len(text.split())} words, {elapsed:.1f}s")

        if chapter_delay > 0 and i < len(CHAPTER_BEATS):
            time.sleep(chapter_delay)

    return story


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--char-a", required=True)
    parser.add_argument("--char-b", required=True)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--out", default="data/story_output.json")
    parser.add_argument("--chapter-delay", type=float, default=0,
                         help="Seconds to wait between chapters. Set this to 5-10 if you "
                              "keep hitting Groq's free-tier rate limit (429 errors) even "
                              "with the automatic retry.")
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not args.smoke_test and not api_key:
        raise SystemExit(
            "No GROQ_API_KEY set. Either export GROQ_API_KEY=<your key>, "
            "or run with --smoke-test to validate the pipeline without one."
        )

    print(f"Generating story: {args.char_a} x {args.char_b} "
          f"({'SMOKE TEST' if args.smoke_test else 'LIVE'})")
    story = generate_story(args.char_a, args.char_b, api_key=api_key,
                            smoke_test=args.smoke_test, chapter_delay=args.chapter_delay)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2)
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()

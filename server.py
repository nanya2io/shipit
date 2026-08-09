"""
ShipIt.exe - Local Server
============================
Runs a small local web server so the dashboard can generate NEW character
pairs live, in the browser, without ever exposing GROQ_API_KEY to the
client. The key stays in this process's environment; the browser only
ever talks to this server over localhost.

Why this exists: dashboard.html on its own is a static file. Making it
"live" without a server would mean putting your API key directly in the
page's JavaScript, which anyone opening dev tools (or the page source)
could read. This server is the fix -- it sits between the browser and
Groq, holding the key itself.

Usage:
    1. Set your key -- either:
       a) Create a .env file in this folder containing:
              GROQ_API_KEY=your-key-here
          (this is loaded automatically on startup, see load_dotenv() below)
       b) Or export it directly in your shell:
              export GROQ_API_KEY="your-key-here"   (Mac/Linux)
              $env:GROQ_API_KEY = "your-key-here"    (PowerShell)
    2. Start the server:   python server.py
    3. Open your browser to: http://localhost:5000
       (NOT dashboard.html directly -- double-clicking the file bypasses
       the server entirely and the Compile Story button will fail.)

What it does NOT do: run Attention Lens live (it needs to download GPT-2
on first use, which is slow and network-heavy for a live button-click).
Run 04_attention_lens.py separately if you want that panel populated --
the dashboard already handles its absence gracefully.
"""
import importlib.util
import os
import re
import sys
import time
import traceback
import urllib.parse

import requests
from flask import Flask, jsonify, request, send_from_directory

try:
    from dotenv import load_dotenv
    # Loads variables from a local .env file (if present) into the real
    # process environment, so GROQ_API_KEY doesn't need to be manually
    # exported every session. Safe to leave in for deployment too --
    # Render (or any host) sets real env vars directly, and load_dotenv()
    # simply does nothing if no .env file exists.
    load_dotenv()
except ImportError:
    # python-dotenv isn't installed -- fall back to requiring a real
    # exported env var, same as before. Doesn't break anything.
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    """Import a sibling script (e.g. 01_generate_story.py) as a module.
    Uses spec_from_file_location because these filenames start with a
    digit and aren't valid Python identifiers for a normal `import`."""
    path = os.path.join(SCRIPT_DIR, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


print("Loading pipeline modules...")
gen_mod = load_module("gen_mod", "01_generate_story.py")
classify_mod = load_module("classify_mod", "02_classify_tropes.py")
brainrot_mod = load_module("brainrot_mod", "03_brainrot_mode.py")
print("Modules loaded.")

WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"


def fetch_character_portrait(name):
    """Look up a free thumbnail for a character via Wikipedia's public
    REST summary API. No key required, and this runs server-side so it
    follows the same "key/network calls stay on the server" pattern as
    the Groq calls above.

    Returns a dict {"image": url_or_None, "wiki_url": url_or_None,
    "title": resolved_title_or_None} -- never raises. Obscure names,
    disambiguation pages, or network hiccups just come back with
    image=None so the frontend can fall back to a placeholder.
    """
    fallback = {"image": None, "wiki_url": None, "title": None}
    if not name:
        return fallback

    url = WIKIPEDIA_SUMMARY_URL.format(urllib.parse.quote(name.replace(" ", "_")))
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "shipIT-dashboard/1.0 (local demo tool)"},
            timeout=5,
        )
        if resp.status_code != 200:
            return fallback
        data = resp.json()
    except (requests.RequestException, ValueError):
        return fallback

    # "disambiguation" pages (e.g. a name that matches several unrelated
    # things) don't have a single character to portrait -- skip rather
    # than show a random/wrong image.
    if data.get("type") == "disambiguation":
        return fallback

    thumbnail = data.get("thumbnail") or {}
    return {
        "image": thumbnail.get("source"),
        "wiki_url": (data.get("content_urls") or {}).get("desktop", {}).get("page"),
        "title": data.get("title"),
    }


app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(SCRIPT_DIR, "dashboard.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({
            "error": "GROQ_API_KEY is not set on the server. Stop this server, "
                     "set the environment variable, and restart it."
        }), 500

    payload = request.get_json(silent=True) or {}
    char_a = (payload.get("char_a") or "").strip()
    char_b = (payload.get("char_b") or "").strip()
    if not char_a or not char_b:
        return jsonify({"error": "Both character names are required."}), 400

    try:
        t0 = time.time()
        print(f"Generating: {char_a} x {char_b} ...")
        story = gen_mod.generate_story(char_a, char_b, api_key=api_key, chapter_delay=2)

        taxonomy = classify_mod.load_taxonomy()
        classified = classify_mod.classify_story(story, taxonomy)

        for i, chapter in enumerate(classified["chapters"]):
            chapter["brainrot_text"] = brainrot_mod.brainrot_rewrite(
                chapter["text"], chapter["title"], api_key=api_key
            )
            # Small gap between calls so brainrot rewrites (which fire right
            # after 4 story-generation calls, same minute) don't immediately
            # trip Groq's free-tier per-minute limit.
            if i < len(classified["chapters"]) - 1:
                time.sleep(2)

        structural_summary = {}
        for chapter in classified["chapters"]:
            structural_summary[chapter["structural_role"]] = [
                t["trope_name"] for t in chapter.get("detected_tropes", [])
            ]

        result = {
            "meta": {
                "note": f"Live-generated via server.py in {time.time() - t0:.1f}s.",
                "attention_note": "",
            },
            "taxonomy": taxonomy,
            "story": classified,
            "structural_summary": structural_summary,
            "portraits": {
                "char_a": fetch_character_portrait(char_a),
                "char_b": fetch_character_portrait(char_b),
            },
        }
        print(f"Done in {time.time() - t0:.1f}s.")
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("\n*** WARNING: GROQ_API_KEY is not set. ***")
        print("The server will start, but /api/generate will fail until you set it "
              "and restart.\n")
    else:
        print("GROQ_API_KEY detected. Ready to generate.")

    print("\nOpen http://localhost:5000 in your browser (not dashboard.html directly).\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

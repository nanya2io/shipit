# ⚡ ShipIt.exe — AI Fanfiction Trope Compatibility Engine

**MSc AI/ML Mini Project — Christ (Deemed to be University), Department of MCA**

---

## 1. What's in this package

| File | What it is |
|---|---|
| `ShipIt_Project_Proposal.docx` | Formal one-pager for your professor's re-approval (research question, methodology, timeline, feature classification). |
| `trope_taxonomy.json` | 16 curated fandom tropes with definitions + detection markers, modeled on AO3's tagging conventions. |
| `01_generate_story.py` | Chapter-by-chapter story generator (Llama 3.1 via Groq API). |
| `02_classify_tropes.py` | Per-chapter trope classifier — **fully tested, real code**, no mocking. |
| `03_brainrot_mode.py` | Register-shift rewriter (Lore Mode → Brainrot Mode) preserving plot. |
| `04_attention_lens.py` | Offline GPT-2 self-attention extraction, feeds the Attention Lens dashboard panel. |
| `server.py` | Local/deployed Flask server — powers the **live** "Compile Story" button end to end (Groq generation → trope classification → brainrot rewrite → Wikipedia character portraits), holding `GROQ_API_KEY` server-side so it's never exposed to the browser. |
| `requirements.txt` | Python dependencies for running/deploying `server.py`. |
| `.env` | **Not committed to git.** Holds your local `GROQ_API_KEY` — see setup below. |
| `demo_story_raw.json` | Hand-authored demo story (Superman × Spider-Man) used to seed and test the dashboard. |
| `dashboard_data.json` | Merged story + real classification output + brainrot rewrites. |
| `dashboard.html` | The interactive dashboard. Can be viewed statically, but **must** be opened via `server.py` (`http://localhost:5000`) for the live Compile Story button and character portraits to work — see below. |

---

## 2. How to run it live (recommended path)

This runs the dashboard as a real local web app, with a working Compile Story button.

1. Get a free Groq API key: [console.groq.com](https://console.groq.com) → API Keys → Create.
2. Create a `.env` file in this folder (same level as `server.py`) containing:
   ```
   GROQ_API_KEY=your-key-here
   ```
   `server.py` loads this automatically on startup — no manual `export` needed. (You can still `export GROQ_API_KEY=...` in your shell instead if you prefer; either works.)
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   python server.py
   ```
5. Open **http://localhost:5000** in your browser (not `dashboard.html` directly — double-clicking the file bypasses the server and the Compile Story button will fail).
6. Type two characters and click **COMPILE STORY** — this calls Groq live, classifies tropes, generates the brainrot rewrite, and looks up character portraits, all server-side.

### Deploying it publicly

The app is also deployed on Render's free tier: `server.py` reads `GROQ_API_KEY` from a real environment variable in production (set in Render's dashboard, not from `.env` — `.env` stays local only and is gitignored). Build command: `pip install -r requirements.txt`. Start command: `gunicorn server:app --timeout 120` (the extended timeout matters — Compile Story can make up to 8 sequential Groq calls with retry/backoff on rate limits, which comfortably exceeds gunicorn's 30s default and gets the worker killed mid-request otherwise).

### Running the offline pipeline manually (optional, advanced)

`server.py` already runs steps 1–3 (generation, classification, brainrot) live per-request. You don't need to run the scripts below unless you want to regenerate the static `dashboard_data.json` demo data, or refresh the Attention Lens panel (which needs `torch`/`transformers` — deliberately kept out of the live server path since it's heavy and slow to cold-start):

```bash
pip install nltk transformers torch matplotlib sentence-transformers
mkdir -p data outputs
python 01_generate_story.py --char-a "Elena" --char-b "Marcus" --out data/story_output.json
python 02_classify_tropes.py --story data/story_output.json --out data/story_classified.json
python 03_brainrot_mode.py --story data/story_classified.json --out data/story_brainrot.json
python 04_attention_lens.py --story data/story_classified.json --out data/attention_lens_data.json
python 06_merge_dashboard_data.py \
  --classified data/story_classified.json \
  --brainrot data/story_brainrot.json \
  --attention data/attention_lens_data.json \
  --out dashboard_data.json
python build_dashboard.py
```

Each step can be skipped if you don't want that feature yet (e.g. omit `--brainrot` or `--attention` in the merge step) — the dashboard just shows fewer panels.

To just **see the demo** without any setup, open `dashboard.html` directly — it already contains a full worked example, though the Compile Story button won't be live without `server.py` running.

---

## 3. What's real vs. what needs your API key

Same honesty principle as your plot-twist project: I validated everything I could without external access.

- **`02_classify_tropes.py` is 100% real, tested code** — it runs fully offline (keyword matching needs no downloads) and I ran it against a hand-written demo story to confirm it produces genuine, non-mocked classifications. It even caught a real bug in my first draft (substring matching flagging "hate" inside "w**hate**ver") — fixed and re-verified.
- **Story generation and Brainrot Mode need your Groq API key** to run live — I can't reach Groq from this sandbox. Both scripts have a `--smoke-test` flag that validates the full pipeline (context-carrying across chapters, file I/O, error handling) with placeholder text, so you know the *code* works before you ever add a key.
- **The demo story in `dashboard.html`** is hand-written by me to a quality bar, then run through the real classifier — so the trope badges and evidence quotes you see are genuine classifier output, not scripted.

---

## 4. LLM Concepts Used (for your report / viva)

Here's every LLM/NLP concept this project actually touches, in plain terms, mapped to exactly where it shows up.

### Autoregressive generation
GPT-style models generate text one token at a time, each new token conditioned on everything generated so far. This is *why* chapter-by-chapter generation works: chapter 2 isn't generated independently — it's conditioned on the literal text of chapter 1, so the model can reference what already happened rather than contradicting itself. Where it shows up: `01_generate_story.py`, the `conversation` list that grows with each chapter.

### In-context learning / conversation as context
Rather than fine-tuning a model on your specific characters, the model learns "who Superman and Spider-Man are" purely from what's already in the conversation history — this is in-context learning. No training happens; the context window *is* the mechanism. Where it shows up: each chapter's API call includes all prior chapters as prior conversation turns.

### System prompts / role conditioning
A `system` message sets persistent behavioral rules (tone, formatting constraints, what not to do) that apply across the whole conversation, distinct from the `user` messages that give the actual task. Where it shows up: `SYSTEM_PROMPT` in `01_generate_story.py` (fiction-writing rules) vs. `BRAINROT_SYSTEM_PROMPT` in `03_brainrot_mode.py` (register-shift rules) — same mechanism, different behavioral contract.

### Prompt engineering / structured instruction design
Each chapter's instruction is deliberately scoped (word count, what to establish, what *not* to resolve yet) rather than a vague "continue the story" — this is what keeps a 4-chapter arc coherent instead of drifting. Where it shows up: the `CHAPTER_BEATS` instruction templates.

### Sampling parameters (temperature, max tokens)
`temperature` controls randomness — lower values make output more predictable/repetitive, higher values more varied/creative. `max_tokens` caps generation length. These are knobs on the *same* underlying autoregressive process, not separate mechanisms. Where it shows up: `call_llm()` in both generation scripts.

### Text embeddings & semantic similarity
Sentence-Transformers converts a sentence into a vector (a list of numbers capturing its meaning). Two sentences with similar meaning end up as vectors that point in a similar direction — measured via **cosine similarity**. This is how trope detection can catch paraphrased tropes that don't use the literal marker words. Where it shows up: `--use-embeddings` mode in `02_classify_tropes.py`; also the entire scoring mechanism in your earlier Movie Plot Twist Predictor.

### Zero-shot classification
The trope classifier never sees labeled training examples of "here's what Enemies-to-Lovers looks like" — it compares each sentence's embedding directly against the trope *definition's* embedding at inference time. This is zero-shot: no task-specific training, just semantic comparison. Where it shows up: `classify_chapter()`'s embedding-similarity branch.

### Explainable AI via evidence grounding
Instead of a bare confidence score, every classification is tied to the *exact sentence* that triggered it. This turns a black-box number into something a person can audit and disagree with. Where it shows up: the `evidence` field on every detected trope, surfaced in the dashboard's hover tooltips.

### Style transfer / controlled generation
Brainrot Mode is a **style transfer** task: change *how* something is said (register, vocabulary, tone) while explicitly preserving *what* is said (plot events, character actions). This is a genuinely distinct NLP problem from open-ended generation — the constraint ("same events, different voice") is the whole point. Where it shows up: `BRAINROT_SYSTEM_PROMPT`'s explicit instruction to preserve plot while changing register.

### Multi-turn dialogue state management
Carrying the full chapter history forward in the `messages` list (rather than just the latest chapter) is the same mechanism that powers any multi-turn chat interface — the "memory" isn't stored anywhere special, it's just re-sent as context on every call. Where it shows up: the `conversation` list growing across the `for` loop in `generate_story()`.

### Self-attention (the mechanism underneath everything above)
Every transformer above — Llama, Mistral, and Sentence-Transformers' MiniLM — is built from **self-attention layers**. For each word in a sentence, self-attention computes how much every *other* word should influence that word's representation, producing a weighted combination rather than reading strictly left-to-right like older RNN models. This is *why* a transformer can connect a character named early in a sentence to a pronoun like "their" appearing three clauses later — attention lets it look at the whole sentence at once and learn which connections matter, rather than only remembering a fixed-size summary as it goes.

Concretely: each word gets three learned vectors — a **Query** (what am I looking for), a **Key** (what do I contain), and a **Value** (what do I offer if picked). A word's new representation is a weighted sum of every other word's Value, where the weights come from comparing that word's Query against every other word's Key. Stack several of these "attention heads" running in parallel (each free to specialize in a different kind of relationship — one head might track grammatical subject/verb agreement, another might track long-range pronoun reference) and you get **multi-head self-attention**, the actual building block inside GPT-2, Llama, Mistral, and BERT-family models alike.

### Attention Lens — a working demo of this mechanism (Enhancement)
`04_attention_lens.py` makes self-attention visible rather than just described. It loads GPT-2, runs a sentence through it with `output_attentions=True`, and extracts the attention weights from the model's final layer — specifically, what the *last token* attended to across the whole sentence, averaged across all attention heads. Normalized to 0–1, this becomes a heatmap: brighter word = more weight the model placed on it.

This slots directly into your Explainable AI story as a second, deeper layer:
- The **evidence-quote system** (already built) shows *which sentence* triggered a trope classification.
- **Attention Lens** shows *which words inside that sentence* the model itself weighted most heavily while processing it — mechanism-level explainability, not just output-level.

**Honesty note, consistent with the rest of this project:** this sandbox can't reach Hugging Face (confirmed — I even checked whether GPT-2's original weights are mirrored anywhere reachable through GitHub/backup hosts; they aren't, from here). So the Attention Lens data currently shipped in `dashboard_data.json` runs on a tiny randomly-initialized GPT-2 architecture — the *code path* is real and fully tested, but the specific weights shown are not a trained model's genuine attention pattern. Run the command below without `--smoke-test` in Colab/Antigravity (where Hugging Face is reachable) to get real attention weights.

**Auto mode (recommended):** rather than picking sentences by hand, point it at a classified story and it automatically runs Attention Lens on each chapter's top-scoring trope's evidence sentence:
```bash
python 04_attention_lens.py --story data/story_classified.json --out data/attention_lens_data.json
```
This output feeds directly into `06_merge_dashboard_data.py --attention`. Chapters with no detected tropes are skipped rather than faked.



## 5. Feature classification (from the proposal)

| Feature | Class |
|---|---|
| Trope taxonomy + chapter generation + classification + structural analysis | Core |
| Bond Meter, chapter-reveal UI, Brainrot Mode, polish pass, flagship demo pairs | Enhancement |
| Live AO3 scraping, user-submitted pairs at runtime | Future Scope |

Full detail in `ShipIt_Project_Proposal.docx`.

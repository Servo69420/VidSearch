# Cost-saving mechanisms (chat/vision pipeline)

This branch ports three OpenRouter cost levers from the sibling project into
VidSearch's existing backend. Everything here is **backend-only**; no frontend
files were touched.

## What was added

### 1. `reasoning_effort` tuning
Many OpenRouter models bill hidden reasoning tokens. `model_config.py` now
exposes `reasoning_effort_chat` (default `low`) and `reasoning_effort_vision`
(default `medium`), threaded through `_call_openrouter` →
`body["reasoning"] = {"effort": ...}`. Models that don't support reasoning
(e.g. Gemma) ignore it silently. Override via `OPENROUTER_REASONING_EFFORT_CHAT`
/ `OPENROUTER_REASONING_EFFORT_VISION`.

### 2. Cheap frame-description model
`vision_description_model` (default `google/gemini-2.5-flash-lite:nitro`,
override `OPENROUTER_VISION_DESCRIPTION_MODEL`) — a low-cost multimodal model
used only to produce a reusable, question-agnostic description of a frame.

### 3. Frame-analysis cache (the behavior change)
New `frame_captures` table (see `schema.sql` + idempotent
`migrations.ensure_frame_captures`, applied on startup in `database.connect()`).

Flow in `POST /chat/ask` when a frame + `current_time_s` are present:
- **First ask about a frame** → answer from the image with the vision model
  (as before), create a `frame_captures` row, and fire a background
  `_describe_and_persist_background` task that stores a cheap description.
- **Later asks near the same timestamp** (within `frame_cache_bucket_s`, default
  2.0s, override `FRAME_CACHE_BUCKET_S`) → inject the stored description as
  context and **skip the image**, answering with the cheaper chat model.

This is the actual saving: repeat questions about the same frame stop
re-sending the image to the vision model. It is a behavior change — the model
answers from cached text instead of a fresh image, so answer quality on
follow-ups depends on the description's fidelity.

Note on the tradeoff: the **first** ask about a frame now costs the vision
answer **plus** the cheap describe call, so net savings only appear at **≥2
asks per frame**. A single-ask-per-frame usage pattern is a slight cost
*increase*. A hit also requires the two asks to fall within
`frame_cache_bucket_s` (2.0s) of the same timestamp — i.e. follow-ups on a
paused/near-static frame, not while the video is scrubbing past.

## What was intentionally NOT ported
- **Confidence-gated vision fallback** (cheap-primary → escalate-to-expensive on
  low confidence). In the source project its trigger keys off *draw-call*
  confidence. VidSearch's tools are play/pause/seek/mute/unmute — there are no
  draw calls, so the trigger could never fire. Porting it verbatim would have
  shipped dead code, so it was omitted.

## Verification status (read before merging)
- **Unit-verified offline:** the full suite passes (127 tests, incl. new
  `tests/test_chat_cost.py` covering reasoning-effort body shape + threading,
  the frame-cache get-or-create hit/miss/failure paths, `_describe_frame`, and
  the new config fields). Run: `python -m unittest discover -s tests` (or
  `pytest tests`).
- **NOT verified end-to-end here:** a live cache hit, the actual drop in token
  cost, and follow-up answer quality were *not* exercised — that needs a real
  OpenRouter key + Postgres + transcribed video. Please confirm those live
  before relying on the savings.

# idea-to-video — Vision · Roadmap · Evaluation

Research date: April 2026.

---

## The Honest Critique of Your Own Request

You asked for "best UX for idea-to-video." That's the wrong frame.

"Best UX" optimizes the interface around a workflow that already exists.
The real question is: **what workflow should exist that doesn't yet?**

Every tool in this space — HeyGen, Runway, InVideo AI, Sora, Kling — has already
solved "given a finished script and creative direction, produce a video fast."
That problem is commoditized. Wan 2.1 is Apache-licensed and matches Sora on benchmarks.
The generation layer is becoming free infrastructure.

The unsolved problem is earlier: **"I have a half-formed idea and a recording of myself
talking about it. Help me think it into a video."** That's the step before every current
tool starts. Nobody owns it. That's where you build.

---

## Competitive Reality

### What Exists (and What It Actually Does)

| Tool | Real Strength | Real Failure |
|------|--------------|--------------|
| **HeyGen** | Avatar realism, 175-language lip-sync | Assumes clean script; no idea development |
| **Synthesia** | Enterprise governance, LMS export | 10 min/month on entry plan; no creative mode |
| **Runway Gen-4** | Filmmaker B-roll, camera control | 30% good output; 10s clip cap; no narrative |
| **InVideo AI** | Fastest idea→draft (2-7 min) | Topically correct, narratively flat; credit burn |
| **Sora** | Best physical world simulation | No audio; no multi-scene coherence; $200/mo |
| **Kling** | Longest clips (2 min), strong physics | UI rough; no workflow beyond clip |
| **LTX Studio** | Script→storyboard→character-consistent shots | Requires structured input; expensive |
| **Descript** | Transcript-first editing | Needs existing footage; not generative |
| **Opus Clip** | Long-form→short clips | No idea-to-video; Trustpilot 2.4/5 |

### The Unpopulated Quadrant

```
                 HIGH CREATIVE CONTROL
                        │
         Runway         │    LTX Studio
         Sora           │  (script→shots)
                        │
GENERATIVE ─────────────┼──────────────── STRUCTURED / AVATAR
(B-roll)                │             (presenter-led)
                        │
         Kling, Luma    │  HeyGen   Synthesia
                        │
                 LOW CREATIVE CONTROL
                        │
       InVideo AI       │  Pictory   Captions.ai
       (idea→draft)     │
```

**Nobody lives here:** high creative control + structured output + conversation as input.
LTX Studio is moving left-to-right. HeyGen is moving bottom-to-top.
You can build to that quadrant faster than either can pivot.

### The Open Source Collapse

The generation moat is gone:
- **Wan 2.1** (Alibaba, Apache 2.0): beats Sora on VBench at 84.7%, runs on 8GB VRAM
- **LTX-Video 2**: 4K/50fps, real-time iteration on RTX 4090
- **CogVideoX, Mochi**: near-commercial quality

**Implication:** Don't invest engineering time in generation quality.
Integrate open models as a commodity. Build the workflow layer.

---

## The Real UX Opportunity

### What Power Users Are Doing (That Tools Don't Support)

1. **Pre-prompting with brand docs.** Paste brand guidelines into ChatGPT before generating — every session, manually. Tools don't persist this.
2. **Multi-model pipelines.** Kling for realistic people → Runway for cinematic B-roll → ElevenLabs for voice → Descript for cleanup → 5 subscriptions, 5 learning curves.
3. **Character sheets as image references.** Midjourney → character image → feed to Kling as reference. Workaround for absent persistent character identity.
4. **Manual A/B hook testing.** Generate 5 versions of the first 3 seconds, test CTR, invest in winner. No tool supports systematic hook testing.

### What Every User Is Saying (Verbatim Patterns)

- *"AI follows topics but ignores dramatic pacing — no escalation, no emotional payoff"* — Motion Agency, Feb 2025
- *"Context loss across sessions — close the tab, start from scratch"*
- *"Credit model punishes exploration — you converge prematurely to avoid burning credits"*
- *"Character consistency breaks the moment you need more than one clip"*
- *"Five subscriptions to produce one video. This can't be the answer."*

### The Core Insight

> Every current tool treats video creation as a **production task**.
> The real opportunity is treating it as a **thinking task**.

The hardest part of making a video isn't rendering — it's figuring out:
- What's the point?
- Who's watching?
- What do they need to feel at the end?
- What's the sequence of ideas?

No tool helps with this. ChatGPT does, but it has no video output.
That gap is yours.

---

## Vision

**One conversation turns into a complete, brand-consistent, multi-scene video.**

Not "paste your finished script here." A genuine back-and-forth:
*"What's this video about?" → "Who's watching?" → "What should they do after?"*
— then structure, storyboard, voices, visuals, and final render emerge from that dialogue.

The user never touches a timeline. They never specify a codec.
They think out loud. The system builds.

---

## Roadmap: Vision → Action → Eval

### Phase 1 — Nail the Core Loop ✅ COMPLETE
*Make the existing pipeline actually usable end-to-end.*

**Actions:**
- [x] Replace `transcribe.py` with WhisperX: speaker diarization + word-level timestamps in one swap
- [x] Add mic recording (Tab 1 + Tab 7 primary audio input)
- [x] Fix extract_topics → write_script → TTS chain so the full pipeline runs without errors
- [x] Add a "Run Full Pipeline" button (Tab 7) that chains all 5 stages with stage-named progress
- [x] Store brand context (name, tone, audience) in `brand.json` — pre-load into every Claude prompt
- [x] Replace uniform slide timing in `make_video.sh` with per-section TTS duration-driven cuts
- [x] Add `write_script_sections()` — one spoken paragraph per topic for timestamp-accurate slides
- [x] GEval quality tests: `tests/eval/test_phase1_quality.py` with deterministic + LLM-judge metrics

**Eval:**
- ✅ Can go from a 2-minute voice recording to a watchable video in under 5 minutes
- ✅ Script sounds natural (GEval threshold 0.60+ across all quality dimensions)
- ✅ Slide transitions match speech rhythm (per-section TTS durations drive ffmpeg cuts)

---

### Phase 2 — Conversation as Input ✅ COMPLETE
*Replace the blank text box with a creative director dialogue.*

**Actions:**
- [x] Pre-production dialogue module (`preproduction.py`): goal / audience / emotion / CTA — saved to `preproduction.json`, prepended before brand context in every Claude prompt (Tab 8 + inline accordion in Tab 7)
- [x] Persistent session context (`session.py`): full pipeline state auto-saved to `~/.idea-to-video/sessions/` on every successful run; "Resume last session" button in Tab 7 restores transcript + topics + script
- [x] Storyboard draft mode: "Storyboard preview" accordion in Tab 3 shows card-per-slide view (title + section text + image prompt) before committing to TTS
- [x] Stage-named progress in Tab 7: "Step N/5 · [stage name]" in both progress bar and log
- [x] "Free to iterate" messaging: cost estimate label under Run button; only Claude API (~$0.01/run) costs money
- [x] `extra_context` param added to `extract_topics()`, `write_script()`, `write_script_sections()` — backward-compatible
- [ ] Topic → image prompt → image generation: integrate SDXL or Flux locally (deferred to Phase 3)
- [ ] Multi-speaker support: WhisperX diarization → assign different Kokoro voices per speaker (deferred to Phase 3)

**From competitive UX research (COMPETITIVE-UX.md):**
- [x] REC-1: Pre-production dialogue (4 questions before generation) — `preproduction.py` + Tab 8
- [x] REC-2: Draft-first mode (storyboard before TTS) — storyboard accordion in Tab 3
- [x] REC-3: Eliminate credit anxiety — "Free to iterate" label + cost estimate in Tab 7
- [x] REC-4: Session persistence — `session.py` + auto-save + Resume button
- [x] REC-5: Recording-first UI — Tab 7 hero redesigned around mic input
- [x] REC-6: Stage-named progress — "Step N/5 · [stage]" throughout pipeline
- [x] REC-7: Brand voice before/without comparison toggle — "Brand impact" accordion in Tab 3 with word-level diff HTML
- [x] REC-8: Settings page with detailed cost estimator — Tab 9 with model selector, per-model pricing, live cost estimate

**Eval:**
- Does pre-production context change what Claude generates? (Compare script divergence with/without)
- Does a user with zero editing experience complete a video in their first session?
- Do users re-use the tool the next day? (Session save rate = retention signal)

---

### Phase 3 — Narrative Coherence ✅ COMPLETE (April 2026)
*Make multi-scene videos that don't fall apart.*

**Actions:**
- [x] Scene graph lite (`session.build_scene_graph`): zip topics + sections + image paths + durations into structured scene dicts; saved in every full pipeline session
- [x] Image generation (`generate_images.py`): Pillow title cards (1920×1080) with gradient bg, badge, title, image prompt; DALL-E 3 backend optional; auto fallback to Pillow when no API key; integrated in Tab 3 storyboard accordion and Tab 7 pipeline step 3.5
- [x] Hook A/B testing (`hook_variants.py`): generate 3 opening variants (Curiosity / Empathy / Authority) via Claude; Tab 3 "Hook variants" accordion; pick → prepend to script
- [x] Brand comparison (REC-7): Tab 3 "Brand impact" accordion; side-by-side word-level diff of script with vs without brand context
- [ ] Character consistency layer: persistent character image embeddings fed to every image generation call (deferred)
- [ ] Semantic editing: "make this section more urgent" → re-generates affected scenes, not the whole video (deferred)
- [ ] Open model video generation: integrate Wan 2.1 for animated clips to replace static image slideshows (deferred)

**Eval:**
- Watch the output video cold (no context) — does it tell a coherent story?
- Does the selected hook measurably change the opening feel of the video?
- Does the brand diff show clear additions that match the brand tone?

---

### Phase 4 — Platform (started April 2026)
*The workflow that replaces the 5-subscription stack.*

**Actions:**
- [x] Clip repurposing (`repurpose.py`): long video → per-scene clips via ffmpeg; merge_short_scenes greedy grouping; Tab 10 "Repurpose" with video input, scenes JSON auto-fill, max-duration slider, ZIP download
- [x] Settings persistence (`settings.py`): Claude model selector, Whisper backend, cost estimator; Tab 9; settings read by all Claude-calling handlers
- [x] API enabled: `demo.launch(show_api=True)` exposes Gradio API for programmatic access
- [ ] Brand memory: persistent store of visual identity, tone, audience, past scripts — loads automatically (deferred)
- [ ] Multi-language: WhisperX transcript → write_script in target language → Kokoro zh/en TTS → localized video (deferred)
- [ ] Collaboration: shared brand context, multiple contributors, version history (deferred)

**Eval:**
- Does a team of 3 non-technical people produce 10 videos/week without a video editor?
- Is the output quality good enough to post without manual cleanup?
- Do users cancel their other subscriptions?

---

## What to Build First (The Honest Prioritization)

The highest-leverage single change is not in the UI.
It's adding **brand context** to every Claude prompt.

Right now the pipeline is stateless — every run starts from scratch.
Add 10 lines: read a `brand.json` file (name, audience, tone, style notes),
prepend it to every `extract_topics` and `write_script` call.
The output quality jump will be larger than any UI improvement.

Second: **replace uniform slide timing with word-timestamp cuts.**
The current video feels like a slideshow because images change on a timer, not on speech.
WhisperX gives you word-level timestamps. Use them. This alone makes the output feel alive.

Third: **the pre-production dialogue.** Four questions before generation.
Not a form — a conversation. This is where the 10x product lives.

---

## What This Is Not

- Not a Runway competitor (you don't own generation quality)
- Not a HeyGen competitor (you don't own avatar realism)
- Not an editing tool (you don't own timeline workflows)

**This is a thinking tool that happens to produce videos.**
The category doesn't exist yet. That's the point.

---

## Phase 3.5 — Visual Generation Strategy (Research + Implementation)

*Research date: April 2026. Replaces static JPG/title-card requirement.*

### The Problem

The current pipeline requires users to either upload JPG images or accept plain dark title cards.
Both are dead ends: uploaded images require pre-existing assets, title cards look like a prototype.
The market has moved: in 2026 generic stock footage carries an "AI slop" signal on YouTube's
algorithm. Users want visuals that actually match their content — not just the first search result
for "productivity."

### Research: What Competitors Do For Visuals

| Tier | Tools | Method | Verdict |
|------|-------|--------|---------|
| **1 — Full synthesis** | Sora, Kling 2.0, LTX-2.3, Runway Gen-4 | Text → video from scratch | Commercial quality; expensive; requires GPU or $0.60+/clip |
| **2 — Stock + AI match** | InVideo AI, Pictory | 3–16M stock assets, AI keyword match | "Generic" complaint is universal; stock look = low credibility by 2026 |
| **3 — Avatar-led** | HeyGen, Synthesia | Talking head is the video | Requires clean script; no idea development |
| **We are here** | idea-to-video | Static title cards or uploaded JPGs | Zero friction, zero quality |

### Research: Open-Source Video Generation (Mac Reality Check)

Local T2V on Apple Silicon is **not practical for an unattended pipeline** today:

| Model | Stars | License | Mac Local | Min RAM | API Option | Cost/clip |
|-------|-------|---------|-----------|---------|------------|-----------|
| Wan 2.1 14B | 15.7K | Apache 2.0 | ✗ (needs 180 GB) | 180 GB | fal.ai, Replicate | $0.20–0.40 |
| Wan 2.1 1.3B | 15.7K | Apache 2.0 | ⚠ (MPS fallback, slow) | 32 GB | fal.ai, Replicate | $0.20 |
| LTX-2.3 | 9.8K | Apache 2.0 | ⚠ (via native Mac app, 32 GB) | 32 GB | fal.ai | $0.06–0.12/s |
| CogVideoX-5B | ~10K | Apache 2.0 | ⚠ (20× slower than GPU) | 32 GB | Replicate | $0.40 |
| AnimateDiff | 12.1K | Apache 2.0 | ✓ (MPS, 16 GB, I2V) | 16 GB | Replicate | $0.10 |
| HunyuanVideo | ~13K | Non-commercial | ✗ (128 GB RAM) | 128 GB | fal.ai | $0.30 |

**Conclusion:** for a solo Mac developer, local T2V generation is viable only for experimentation.
The production path is a cloud API with a local fallback chain.

### Research: Free Stock APIs

| API | Free tier | Video? | Rate limit | Key insight |
|-----|-----------|--------|------------|-------------|
| **Pexels** | Unlimited (req attribution) | ✓ HD + 4K MP4 | 200 req/hr, 20K/month | Best: direct MP4 download links, hotlink OK |
| **Unsplash** | 50 req/hr (demo) / 5K (production) | ✗ photos only | 50–5K/hr | Best photo quality; must trigger download event |
| **Pixabay** | 100 req/min | ✓ + illustrations | 100/min | No hotlink; must cache server-side |

### The Market Signal

Users on Reddit/YouTube/ProductHunt 2025-2026 in priority order:
1. **Own footage** (screencast, webcam) — highest trust signal
2. **AI-generated that actually matches** — willing to pay $0.20–0.50/clip if visually coherent
3. **Well-curated stock** — acceptable if not obviously generic
4. **Auto-selected stock** — "I can always tell it's InVideo AI"

The "stock look" is now an active YouTube algorithmic risk (AI labeling policy 2026).
Users want *control* over what visual goes with each section, not auto-selection.

### The Fallback Chain (What We Build)

```
For each scene:
  1. User-uploaded images/video  → use as-is (existing)
  2. Ken Burns effect            → animate title cards with ffmpeg pan+zoom (free, no API)
  3. Pexels stock video          → search by image_prompt keyword, download best MP4 (free, PEXELS_API_KEY)
  4. fal.ai Wan 2.1              → AI generate 5s clip from image_prompt ($0.20, FAL_KEY)
  5. Pillow title card           → fallback of last resort (always works)
```

"Auto" mode walks the chain from #2 down based on available API keys.
The user can pin any source per-run from Tab 7 or Tab 9.

### Phase 3.5 — Actions

- [x] `visual_sources.py` — unified visual acquisition with fallback chain (Ken Burns → Pexels → fal.ai → title card)
- [x] `assemble_video.py` — replace `make_video.sh` for video-clip inputs; handles both image slideshows and MP4 clip concat via ffmpeg
- [x] Ken Burns effect: ffmpeg `zoompan` filter on each title card — `scale=8000:-1` pre-step, `z='min(zoom+0.0015,1.5)'`, `s=1920x1080:fps=25` — produces cinematic animated slide, zero new deps
- [x] Pexels integration: `GET /videos/search?query={image_prompt}&per_page=3&orientation=landscape` → download first `sd` quality MP4 → fallback to kenburns on empty results
- [x] fal.ai integration: `fal-ai/wan-t2v` with `image_prompt` as prompt, 480p, 81 frames; guarded by try/except ImportError
- [x] Tab 7: "Visual source" dropdown — Auto / Ken Burns / Pexels / fal.ai / Pillow
- [x] Tab 9: API key status fields for PEXELS_API_KEY and FAL_KEY (read-only, from env)
- [x] Update `run_full_pipeline` to call `visual_sources` instead of `_make_slide_images`

**Eval:**
- Does the Ken Burns effect make the output look like a real YouTube video vs a slideshow?
- Does Pexels stock retrieval return visually relevant clips >70% of the time for typical topics?
- Is total pipeline cost with fal.ai clearly shown before running?
- Does the fallback chain degrade gracefully when API keys are missing?

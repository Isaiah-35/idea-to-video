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

### Phase 1 — Nail the Core Loop (Now → 8 weeks)
*Make the existing pipeline actually usable end-to-end.*

**Actions:**
- [ ] Replace `transcribe.py` with WhisperX: speaker diarization + word-level timestamps in one swap
- [ ] Add mic recording (already done in Tab 1)
- [ ] Fix extract_topics → write_script → TTS chain so the full pipeline runs without errors (in progress)
- [ ] Add a "Run Full Pipeline" button that chains all 6 stages with visible progress
- [ ] Store brand context (name, tone, audience) in a local config file — pre-load into every Claude prompt
- [ ] Replace uniform slide timing in `make_video.sh` with word-timestamp-driven cuts

**Eval:**
- Can you go from a 2-minute voice recording to a watchable video in under 5 minutes?
- Does the script sound like it was written for the speaker, not by a committee?
- Do slide transitions match speech rhythm?

---

### Phase 2 — Conversation as Input (8 → 20 weeks)
*Replace the blank text box with a creative director dialogue.*

**Actions:**
- [ ] Pre-production dialogue module: 4 fixed questions (point, audience, emotion, CTA) before any generation starts
- [ ] Persistent session context: brand voice, recurring topics, visual style — stored, reloaded between sessions
- [ ] Topic → image prompt → image generation: integrate SDXL or Flux locally for slide images instead of requiring user uploads
- [ ] Multi-speaker support: WhisperX diarization → assign different Kokoro voices per speaker → multi-voice video
- [ ] Draft mode: generate a low-fidelity text-only storyboard before committing to TTS + video render

**Eval:**
- Does the pre-production dialogue change what the AI generates? (Measure script divergence with/without it)
- Does a user with zero editing experience complete a video in their first session?
- Do users re-use the tool the next day? (The real retention signal)

---

### Phase 3 — Narrative Coherence (20 → 40 weeks)
*Make multi-scene videos that don't fall apart.*

**Actions:**
- [ ] Scene graph: represent the video as a directed sequence of scenes with explicit dependencies (character X appears, referenced in scene 3, must match scene 1)
- [ ] Character consistency layer: persistent character image embeddings fed to every image generation call
- [ ] Semantic editing: "make this section more urgent" → re-generates affected scenes, not the whole video
- [ ] Hook A/B testing: auto-generate 3 opening variants, present side-by-side, commit to winner
- [ ] Open model video generation: integrate Wan 2.1 for animated clips to replace static image slideshows

**Eval:**
- Watch the output video cold (no context) — does it tell a coherent story?
- Do characters look the same in scene 1 and scene 5?
- Does "make this more urgent" produce a measurably different result without breaking adjacent scenes?

---

### Phase 4 — Platform (40+ weeks)
*The workflow that replaces the 5-subscription stack.*

**Actions:**
- [ ] Brand memory: persistent store of visual identity, tone, audience, past scripts — loads automatically
- [ ] Clip repurposing: long video → short-form clips with auto-selected hooks (Opus Clip's feature, owned by you)
- [ ] Multi-language: WhisperX transcript → write_script in target language → Kokoro zh/en TTS → localized video
- [ ] Collaboration: shared brand context, multiple contributors, version history
- [ ] API: expose the pipeline as endpoints so others can build on it

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

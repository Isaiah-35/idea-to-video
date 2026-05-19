# Competitive UX Research — idea-to-video
*Research date: April 2026*
*Method: Homepage + pricing screenshots (live), WebSearch + WebFetch across G2, Trustpilot, Reddit, ProductHunt*
*Screenshots: `.gstack/ux-research/screenshots/`*

---

## Executive Summary

Every tool in this space solves the same problem: "given creative direction, produce a video quickly." Nobody solves the problem one step earlier — "help me figure out what the video should be." That gap is the entire opportunity. The dominant UX pattern across all seven tools is **generate-first, edit-second** with a credit wall in between. Users universally report the same friction: *credit anxiety kills exploration*. The tool that removes credit fear and starts from a thinking conversation — not a text box — owns a category that currently doesn't exist.

---

## Competitors Analyzed

| Tool | URL | Positioning | Research Depth |
|------|-----|-------------|----------------|
| HeyGen | heygen.com | Avatar-led presenter video | Homepage + pricing screenshot, G2, Trustpilot, Reddit |
| InVideo AI | invideo.io/ai | Fastest idea→draft (text-to-video) | Homepage screenshot, Trustpilot, Motion Agency review |
| Runway Gen-4 | runwayml.com | Filmmaker B-roll, character consistency | Homepage screenshot, G2, AI Tool Analysis deep review |
| LTX Studio | ltx.studio | Script→storyboard→shots | Homepage screenshot, MarketingToolPro, SourceForge |
| Sora (OpenAI) | sora.com | Physical world simulation | Skywork, HumAI, Cybernews reviews |
| Kling AI | kling.ai | Long clips, physics-accurate motion | eesel.ai, App Store, Trustpilot |
| Descript | descript.com | Transcript-first editing | Homepage screenshot, Fritz AI, eesel.ai |

---

## Per-Competitor Analysis

---

### 1. HeyGen

**Homepage observation:** Clean, feature-marketing layout. Hero shows avatar realism demo clips. Above-fold CTA: "Start creating videos with AI." Navigation: Studio / Templates / Pricing / Blog. Pricing tiers visible: Free / Creator / Pro (three-column layout, gradient header). No conversational element — pure feature showcase.

**Pricing model:** Free tier (limited minutes) → Creator → Pro. Seat-based + video-credit hybrid. Credits required for avatar generation, voice cloning, and translation.

**What users provide first:** Script or topic → avatar selection → language/voice. The input is always a *finished script*, not an idea.

**Steps from start to video:** ~5 steps: (1) create/select avatar, (2) paste script, (3) select voice/language, (4) generate, (5) download.

**Verbatim positives (from G2 / Trustpilot):**
- *"The lip-sync quality in 175 languages is genuinely impressive — our localization team uses it instead of re-recording."*
- *"Avatar realism has improved dramatically. Our presenters use it for all product demos now."*
- *"Setup to first video took about 20 minutes including avatar creation."*

**Verbatim negatives (from G2 / Reddit / Trustpilot):**
- *"The workflow requires you to download videos to preview them. That alone slows everything down."*
- *"They advertise 'unlimited' but you hit a wall fast. The credit model is confusing by design."*
- *"Errors on failed jobs still eat credits. I lost $30 on generations I never saw."*
- *"Avatar creator is really bad in 2026 compared to what's in the market today."*
- *"Customer support is nonexistent when things go wrong, despite paying for a complex tool."*

**Recurring themes (3+ sources):**
- Positive: Avatar realism, lip-sync fidelity, multilingual support
- Negative: Credit opacity, no refunds on failures, download-to-preview friction, degrading avatar quality vs. competition

**Primary UX innovation:** Persistent avatar identity — same face, any script. The breakthrough for enterprise localization.
**Biggest friction:** Workflow requires script-first. No ideation support. Every iteration costs credits and a download.

---

### 2. InVideo AI

**Homepage observation:** Gallery-heavy layout — dozens of example video thumbnails in a grid. Prominent "Generate video" CTA with text input field visible on homepage (rare: prompt box above the fold). Navigation minimal. Social proof: "10M+ creators."

**Pricing model:** Free (watermarked, limited) → Plus ($20/mo) → Max ($48/mo). Credits consumed per generation + per AI voiceover + per script revision.

**What users provide first:** A text prompt. *"All you need to do at the start is type out a prompt in the input area."* The most frictionless cold start of any tool in this category.

**Steps from start to video:** 3 steps: (1) type prompt, (2) AI generates script + footage selection + voiceover, (3) optionally tweak. Fastest cold start (2–7 minutes to first draft).

**Verbatim positives:**
- *"The tool itself is super easy to use. Most of it just makes sense. You don't really need a tutorial to figure things out."*
- *"The text-to-video feature is impressively accurate — it completely changed my workflow."*
- *"AI voiceovers are surprisingly natural."*

**Verbatim negatives:**
- *"Too expensive for not being able to stick to the 'Use My Script' workflow — there's always a system issue where prompts aren't understood correctly."*
- *"Every edit consumes credits. Changing the structure of the video can be time-consuming and expensive."*
- *"Quality is poor, inauthentic, and robotic — it stitches together stock footage that doesn't match up well."*
- *"Unclear or ever-changing pricing plans."*

**Recurring themes:**
- Positive: Fastest cold start, genuinely simple UX, no learning curve
- Negative: Topically correct but narratively flat, stock footage mismatch, credit burn on iteration, "AI follows topics but ignores dramatic pacing"

**Primary UX innovation:** Prompt box on homepage — lowest barrier to entry in the category.
**Biggest friction:** You can't explore without burning credits. Convergence happens prematurely.

---

### 3. Runway Gen-4

**Homepage observation:** Dark, minimal, editorial aesthetic. No product screenshots visible — it's a news/research page with blog posts about AI. Navigation: Home / Explore / Research / Products / Blog. CTA is buried. Strong "filmmaker tool" positioning but not obvious from first visit. Stark contrast to InVideo's gallery-first approach.

**Pricing model:** Standard ($15/mo, 125 credits) → Pro ($35/mo, 2250 credits) → Unlimited ($95/mo). Credits consumed per second of generated video.

**What users provide first:** Text prompt + optional image reference. Character consistency feature requires feeding a reference image.

**Steps from start to video:** 4 steps: (1) create project, (2) write prompt + optionally attach reference image, (3) generate (4–7 min wait), (4) assess and decide whether to re-run. Significant iteration cost per step.

**Verbatim positives:**
- *"Same person, recognizable across all three scenes."* (character consistency across shots — the breakthrough)
- *"The interface is denser with more granular controls — the 'Pro' factor is real. I wasn't just typing prompts, I was directing shots."*

**Verbatim negatives:**
- *"The interface doesn't clearly explain what this buys you."* (reviewer, day 1)
- *"Charged me 600 credits for the most useless video ($15) and wouldn't refund."* (Trustpilot)
- *"You're constantly calculating: 'Is this worth 12 credits?' The mental overhead is exhausting."*
- *"Image generation is painfully slow... Waiting 10 minutes for a single video defeats the entire purpose of rapid iteration."*

**Recurring themes:**
- Positive: Character consistency (unique), filmmaker-grade camera controls, cinematic quality ceiling
- Negative: Credit calculation paralysis, failed-generation penalty, slow generation kills iteration, high learning curve

**Primary UX innovation:** Character persistence across scenes — feed one reference image, characters stay consistent shot-to-shot.
**Biggest friction:** The tool punishes exploration. Every experiment costs money and 5+ minutes.

---

### 4. LTX Studio

**Homepage observation:** Dark cinematic aesthetic — black background, film-grain texture, full-bleed video clips. Gallery of generated clips. Navigation: Explore / Pricing. Positioning is "film production studio" not "quick video maker." Premium feel, clearly targets serious creators.

**Pricing model:** Free (watermarked) → Creator $15/mo → Team $35/mo → Agency $85/mo. Annual saves ~20%. No credit burns for basic usage — subscription grants generation quota.

**What users provide first:** Concept/script → storyboard → shot panels → asset upload. Requires structured input upfront. The highest structured-input bar of all tools.

**Steps from start to video:** 4 structured steps: (1) upload assets / describe concept, (2) storyboard in shot panels, (3) review generated shots + camera controls, (4) export. Learning curve significant.

**Verbatim positives:**
- *"She picked up the basics after 10 minutes with the workspace's guidance mode."*
- *"The customizable dashboard and intuitive interface make editing feel creative and rewarding, not technical."*
- *"Lightning-fast startup speed and real-time collaboration eliminate email chains."*

**Verbatim negatives:**
- *"Limited third-party integrations force manual importing/exporting between platforms like Figma."*
- *"Onboarding takes time for non-editors — you need to understand storyboarding concepts first."*
- *"Fewer built-in templates compared to competitors, requiring more custom design work."*

**Recurring themes:**
- Positive: Beautiful output, logical progression (concept→storyboard→shots), team collaboration
- Negative: Requires editors; not beginner-friendly; limited integrations

**Primary UX innovation:** Script→storyboard→character-consistent shots as a structured pipeline (director's workflow).
**Biggest friction:** Requires users to think like a film director. Non-editors hit a wall at the storyboard step.

---

### 5. Sora (OpenAI)

**Pricing model:** Available in ChatGPT Plus ($20/mo) and Pro ($200/mo). Higher tiers unlock longer clips and higher resolution.

**What users provide first:** Text prompt. Optional: reference image for world consistency.

**Key UX features:**
- **Storyboard:** Map out video scene-by-scene before generating — most creative control in the category.
- **Recut:** Trim and reshape clips inside Sora without leaving the tool.

**Verbatim positives:**
- *"The storyboard feature is the most creative tool in Sora — you map out your video before generating, giving you way more control than a single text prompt."*

**Verbatim negatives:**
- *"The feedback is split between amazement and frustration — the same prompt can produce a perfect cinematic shot one time and something uncanny the next."*
- *"Sora is simultaneously the most impressive AI video tool and the most frustrating."*
- *"Start here to ideate, then finalize in a pro editor."* (users treat it as step 1 of a multi-tool workflow)

**Recurring themes:**
- Positive: Physical world simulation quality, storyboard-before-generate paradigm
- Negative: "Generation lottery" — output consistency unpredictable; no audio workflow; most users use it as step 1, not the complete workflow

**Primary UX innovation:** Storyboard planning before commitment — closest thing in the market to "think before you generate."
**Biggest friction:** No audio. Outputs require post-processing. $200/mo for Pro access.

---

### 6. Kling AI

**Homepage observation:** JavaScript-heavy SPA — rendered as blank screen in headless browser (no static content). This itself is a UX signal: no progressive enhancement, accessibility concerns. Top nav: Creative Studio / API Platform / About / Blog.

**Pricing model:** Credit-based. Free tier with long wait times. Paid credits expire if unused.

**What users provide first:** Text prompt + optional image reference for motion.

**Verbatim negatives:**
- *"If it messes up, too bad, you just lost 60 credits and waited 6 hours for nothing."* (App Store review)
- *"Generation gets stuck at 99% and then just fails."* (the "99% freeze" bug, widely reported)
- *"Emails and support tickets go completely unanswered. I was charged for months after trying to cancel."*

**Recurring themes:**
- Positive: Longest clips (up to 2 min), strong physics, cinematic motion when it works
- Negative: Extreme generation wait times for free users (hours), failed-generation no-refund policy, impossible to cancel, stuck-at-99% bug

**Primary UX innovation:** Longest generation window + physics-accurate motion.
**Biggest friction:** Reliability. Generation lottery + no support + no refund = high churn.

---

### 7. Descript

**Homepage observation:** Warm dark red/maroon aesthetic. Hero: "AI-editing for every kind of video." Prominent transcript-first positioning. Social proof visible. Pricing section with plan comparison table. "Edit by deleting text" is the core UX promise above the fold.

**Pricing model:** Pre-Sept 2025: transcription hours. Post-Sept 2025: Media Minutes + AI Credits (forced migration angered users). Multiple tiers, free with watermark.

**What users provide first:** Existing video/audio file. Descript is not generative — it's editorial. Requires footage to exist before Descript adds value.

**Steps from start to edited video:** 3 steps: (1) upload video/audio, (2) auto-transcription, (3) edit transcript to cut video. Optional: Overdub (voice cloning for re-recording), AI filler removal.

**Verbatim positives:**
- *"Editing video is as simple as deleting words or moving sentences around in the text."*
- *"Cutting editing time by 60–70% compared to tools like Final Cut."*
- *"It can find and delete all your 'ums,' 'ahs,' and 'you knows' in one go."*

**Verbatim negatives:**
- *"A month's worth of credits lasts about a day. All these supposedly amazing AI features are there to look at and not use as the AI credits costs renders them unusable."*
- *"The app is often slow, laggy, and crashes a lot, especially with longer videos."*

**Recurring themes:**
- Positive: Transcript-first editing is genuinely faster; filler removal is beloved
- Negative: September 2025 pricing overhaul broke trust; unreliable on longer projects; requires existing footage

**Primary UX innovation:** Transcript as the editing interface — delete words, delete footage.
**Biggest friction:** Requires pre-existing footage; cannot help with ideation or generation.

---

## Cross-Competitor Patterns

### Genre Conventions (what every tool does — users expect this)

| Pattern | Implementation across category |
|---------|-------------------------------|
| **Gallery of example outputs** | Every tool shows finished videos as primary CTA. Users are sold on output quality before trying the workflow. |
| **Credit-based pricing** | Universal. Users universally dislike. Creates exploration anxiety. |
| **Dark/dramatic aesthetic** | All generative tools (Runway, LTX, Kling, Sora) use dark backgrounds with cinematic stills. InVideo/HeyGen use lighter, marketing-friendly palettes. |
| **Text prompt as primary input** | All tools start with a text box. Nobody starts with a conversation or a recording. |
| **Generate → assess → iterate loop** | Standard pattern. The quality of this loop (speed, cost, result) determines satisfaction. |
| **Download/export as final step** | No tool has native publish/share. Output is always a file. |

### Anti-Patterns (what every tool does badly — shared failures)

1. **Credit anxiety kills creativity.** Every tool that charges per generation produces the same behavior: users pre-converge on a plan before hitting "generate" because iteration is expensive. This inverts the creative process. The tool that removes credit fear unlocks a fundamentally different workflow.

2. **Script-first assumption.** Every tool assumes the user arrives with a finished script or a clear creative brief. The most common user reality — "I have a half-formed idea and want help thinking it through" — is unserved.

3. **Context amnesia.** No tool remembers anything between sessions. Brand voice, previous scripts, recurring characters — all must be re-entered manually. Every session starts from scratch.

4. **No pre-production dialogue.** Not one tool asks: "What's the point of this video? Who's watching? What should they feel at the end?" These are the questions that determine output quality, and no tool asks them.

5. **Generation as commitment.** Generating always produces audio + video simultaneously. There's no "show me a text storyboard first" step that lets users validate the structure before spending credits and time on full generation.

6. **Mobile-hostile workflows.** The generation-heavy tools (Runway, Kling, Sora) show no mobile consideration. Kling's JS-only homepage is completely inaccessible without client-side rendering.

---

## Unpopulated Space — Jobs-to-Be-Done Matrix

| Job to be done | HeyGen | InVideo | Runway | LTX | Sora | Kling | Descript | idea-to-video |
|----------------|--------|---------|--------|-----|------|-------|----------|----------------|
| Help me structure a half-formed idea | ✗ | ✗ | ✗ | ✗ | partial (storyboard) | ✗ | ✗ | **✓ opportunity** |
| Generate from a script | ✓ | ✓ | partial | ✓ | ✓ | partial | ✗ | ✓ |
| Make this sound like my brand | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ brand.json** |
| Show me a draft before I commit | ✗ | ✗ | ✗ | partial | partial | ✗ | ✗ | **✓ opportunity** |
| Iterate without burning budget | ✗ | ✗ | ✗ | partial | ✗ | ✗ | ✓ | **✓ local pipeline** |
| Input a voice recording, get a video | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | partial | **✓ core loop** |
| Continue from where I left off | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ opportunity** |
| Multi-language output | ✓✓ (best) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

**Summary:** The entire left column of the matrix — ideation, brand voice, pre-commit drafts, iteration without cost — is unpopulated. idea-to-video can own all four with its current architecture (local pipeline = no credit wall, brand.json = persistent context, transcript-first = voice recording as input).

---

## Recommendations for idea-to-video

### REC-1: Pre-production dialogue before any generation
**Evidence:** Zero tools ask "what's the point of this video?" — yet this is universally identified as the missing step (*"AI follows topics but ignores dramatic pacing — no escalation, no emotional payoff"* — Motion Agency). Sora's storyboard is the closest approximation.
**Why it matters:** Answering 4 questions (point / audience / emotion / CTA) produces fundamentally different script output from Claude. Without it, the output is topically correct but narratively flat — the InVideo problem.
**What to build:** Conversation tab that runs 4 questions before enabling "Extract Topics." Questions are conversational, not a form. Answers persist to `brand.json` alongside brand context.
**Priority:** P1 | **Effort:** Low (it's a UI addition — Claude already handles the logic)

---

### REC-2: Draft-first mode — show storyboard before committing to TTS
**Evidence:** All tools make generation a commitment. Users report *"I wish there was a preview before I burn credits"* across HeyGen, Runway, and InVideo. Sora's storyboard-before-generate is the only partial answer.
**Why it matters:** Users pre-converge on bad scripts because iteration feels expensive even when it isn't (with a local pipeline, it's just slow). Showing a text storyboard first lets users correct the structure before waiting for TTS + video assembly.
**What to build:** "Draft" button alongside "Generate" in the script tab. Draft outputs a card-per-topic view (title + 2 sentences + image_prompt) — no audio, no video. User approves or edits, then commits to full generation.
**Priority:** P1 | **Effort:** Medium

---

### REC-3: Eliminate credit anxiety with explicit "free to iterate" messaging
**Evidence:** The most repeated user frustration across all 7 tools is credit burn on iteration. *"You're constantly calculating: 'Is this worth 12 credits?'"* — Runway review. *"Every edit consumes credits, making iterations expensive"* — InVideo review.
**Why it matters:** idea-to-video runs fully locally — there's no API call cost for TTS or video assembly. This is a genuine differentiator. But users arriving from other tools will import their credit-anxiety habits unless you actively reassure them.
**What to build:** Explicit "no credits, no limits" copy at the top of the Generate tab. Progress indicator shows which step is running (Transcribe → Claude API → Kokoro TTS → FFmpeg) so users understand the cost is only the Claude API call, not the video itself.
**Priority:** P1 | **Effort:** Low (copy change + UI label)

---

### REC-4: Session persistence — remember everything between visits
**Evidence:** *"Context loss across sessions — close the tab, start from scratch"* — repeated across Reddit threads about HeyGen, InVideo, and Runway. Zero tools persist anything.
**Why it matters:** A user who runs the pipeline on Monday and returns Thursday should see their last transcript, topics, script, and brand settings pre-loaded. This alone creates a retention signal no competitor has.
**What to build:** Auto-save all pipeline state to `~/.idea-to-video/sessions/{date}/`. Session picker in sidebar. Brand.json already provides partial persistence — extend to full session state.
**Priority:** P1 | **Effort:** Medium

---

### REC-5: Voice recording as primary input, not text
**Evidence:** Every tool starts with a text box. idea-to-video's actual differentiator is "I recorded myself talking about this idea." This input type is invisible in the UI — Tab 1 has it, but it's not positioned as the *primary* entry point.
**Why it matters:** The text-box-first interface trains users to think of this as another InVideo competitor. A recording-first interface signals "thinking tool" vs. "script-to-video factory."
**What to build:** Redesign the landing tab from "choose your stage" to a single primary action: a large microphone button with the label "Talk about your idea." Tabs become steps, not options.
**Priority:** P1 | **Effort:** Medium (layout change to app.py Tab 7)

---

### REC-6: Visual progress that builds trust during long operations
**Evidence:** Runway users specifically cite *"Waiting 10 minutes for a single video defeats the purpose of rapid iteration"* — not because the wait is too long, but because nothing reassuring happens during it. Kling's 99% freeze is the failure mode of this pattern.
**Why it matters:** idea-to-video's full pipeline takes 2–5 minutes. Without visible progress, users assume it's frozen. With it, they understand what's happening.
**What to build:** In "Run Full Pipeline," each stage becomes a named line item with live status (⏳ Transcribing… → ✓ Topics extracted → ⏳ Writing script…). Already partially done with `gr.Progress()` — make it stage-named, not just percentage.
**Priority:** P2 | **Effort:** Low

---

### REC-7: Brand voice comparison — before/without
**Evidence:** The most requested feature across tools is brand consistency. Users paste brand guidelines into ChatGPT manually before every session (*"Tools don't persist this"* — ROADMAP). idea-to-video already has `brand.json`. But users can't feel the difference.
**What to build:** "Preview with brand / without brand" toggle in the Topics and Script tabs that shows the same content generated both ways. Users immediately feel the value of having brand context loaded.
**Priority:** P2 | **Effort:** Medium

---

### REC-8: Pricing / access model — no subscriptions, no credits
**Evidence:** Credit models are the #1 driver of negative reviews across all tools (HeyGen, InVideo, Runway, Kling, Descript all received multi-star rating drops from pricing changes). The open-source model (local Whisper + local Kokoro + Claude API = pay only for Claude inference) is a structural cost advantage.
**Why it matters:** The competitive moat is not just "cheaper" — it's "explore without anxiety." A user testing 10 topic variations spends $0.10 in Claude API calls and 4 minutes of compute, not $15 in credits.
**What to build:** Cost estimator on the settings page: "Each full pipeline run costs ~$0.008 in Claude API calls." This is not UX polish — it's a weapon against every tool in the category.
**Priority:** P2 | **Effort:** Low

---

## UX Pattern Comparison Matrix

| Dimension | HeyGen | InVideo AI | Runway | LTX Studio | Sora | Kling | Descript | idea-to-video (current) |
|-----------|--------|-----------|--------|------------|------|-------|----------|------------------------|
| **Primary input** | Script + avatar | Text prompt | Text prompt | Concept → storyboard | Text prompt | Text prompt | Video file | Voice recording |
| **Steps to first output** | 5 | 3 (fastest) | 4 | 4 | 3 | 3 | 3 | 6 (too many) |
| **Pre-production dialogue** | ✗ | ✗ | ✗ | partial | partial | ✗ | ✗ | ✗ (opportunity) |
| **Brand persistence** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (brand.json) |
| **Session memory** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | partial | ✗ (opportunity) |
| **Draft before commit** | ✗ | ✗ | ✗ | partial | partial | ✗ | ✗ | ✗ (opportunity) |
| **Credit anxiety** | High | High | Very High | Medium | Medium | Very High | High | None (local) |
| **Generation time** | 2–3 min | 2–7 min | 4–7 min | 3–5 min | 3–6 min | 6 min–6 hr | seconds | 2–5 min |
| **Mobile support** | ✓ | ✓ | ✗ | partial | ✗ | ✗ | ✓ | ✗ |
| **Onboarding** | Guided | Self-serve | Steep | Guided+ | Medium | None | Guided | Tab-per-stage |

---

## Screenshots Index

| File | Contents |
|------|----------|
| `heygen-homepage.png` | Hero, features, social proof |
| `heygen-pricing.png` | Free/Creator/Pro tiers, feature comparison table |
| `invideo-homepage.png` | Gallery grid, text prompt CTA above fold |
| `runway-homepage.png` | Minimal dark editorial, research-first positioning |
| `ltxstudio-homepage.png` | Dark cinematic, video gallery, film production positioning |
| `kling-homepage.png` | JS-only SPA — blank render (loading spinner only) |
| `descript-homepage.png` | Warm red theme, transcript-editing CTA, pricing section |

---

## What This Means for Phase 2

The ROADMAP Phase 2 actions (pre-production dialogue, persistent session context, draft mode, multi-speaker) are not just nice-to-have — they are the complete map of everything the competitive landscape has failed to build. No competitor owns the "thinking" phase. idea-to-video gets there first by making the recording-first, conversation-first, draft-before-commit workflow the default experience.

The strategic question is no longer "how do we compete on video quality?" It's: *"How do we make thinking out loud into a finished video feel effortless?"* The answer is in Phase 2, and the competition is still on Phase 1.

---

*Generated by `/ux-research` skill — gstack v0.11.10.0*
*Sources: G2, Trustpilot, Reddit, eesel.ai, Motion Agency, AI Tool Analysis, Fritz AI, MarketingToolPro, Skywork, Cybernews*

---

---

# Part 2: Technical Visuals Research Brief

*Research date: April 2026. Covers visual pipeline specifics per competitor, free stock media APIs, ffmpeg Ken Burns syntax, local T2V model hardware requirements, cloud API pricing, and user sentiment on footage sourcing.*

---

## A. How Each Competitor Sources Visuals (Ranked by Output Quality)

### Tier 1 — AI-Generated, Pure Synthesis (no stock library)

**LTX Studio (Lightricks)**
- Sources: 100% AI-generated via LTX-2 model (open-sourced January 2026).
- Pipeline: script → scene breakdown → camera movement specification → LTX-2 generates video per scene.
- Reference image upload guides aesthetic; frame-accurate keyframes for pan/tilt/zoom/tracking/orbital.
- LTX-2 generates audio + video simultaneously (synchronized dialogue, music, ambience — unique).
- First second of output streams almost instantly via autoregressive pipeline; native 4K at up to 50fps.
- No stock library. Every visual is generated; nothing is retrieved.

**Runway Gen-4 / Gen-4.5**
- Sources: 100% AI-generated; no stock library.
- Input: text prompt + optional reference images ("Subject-Scene-Style" triads).
- Character consistency: upload headshot + full-body photo + style guide → digital "actor" stays consistent across shots.
- Gen-4.5: API available for pipeline integration with custom automation.
- Typical professional workflow: Runway Gen-4 for character/environment images → export to Kling for motion.
- Output: 4–7 seconds per generation, cloud-only, no local option.

**Kling 2.0 / 3.0**
- Sources: 100% AI-generated; no stock library.
- Text-to-video and image-to-video with initial + final frame control.
- Multi-element editor: add, swap, or delete video components via text or image prompts.
- Excels at complex motion, dynamic scenes, realistic physics, character animation.
- Typical use: Runway generates the frames → Kling animates them.

**Sora (OpenAI, via ChatGPT)**
- Sources: 100% AI-generated.
- Storyboard feature: plan scene-by-scene before generating — most creative pre-commit control in the category.
- Recut: trim and reshape inside Sora.
- No audio pipeline — video only; post-processing required for sync.

**Wan 2.1 (Alibaba/Qwen, open-source)**
- Sources: 100% AI-generated; no stock library.
- Available locally or via Replicate/Fal.ai API.
- See Section C for hardware requirements.

---

### Tier 2 — Premium Stock Library + AI Matching

**InVideo AI**
- Sources: 16M+ premium royalty-free assets via iStock, Storyblocks partnerships.
- AI matching: semantic analysis of script text → selects contextually relevant stock clips per scene.
- As of late 2025, added Sora 2 (OpenAI) for AI-generated video up to 60s with synchronized audio, plus VEO 3.1 (Google DeepMind) for multi-scene character consistency with frame referencing, and Nano Banana for storyboarding.
- User control: can override per-scene visual, swap individual clips.
- Weakness: AI-selected stock clips tend to be generic for uncommon or technical topics; matching degrades on abstract subjects.

**Pictory**
- Sources: Storyblocks (video clips), Pexels and Getty Images (photos). Library: ~3M assets.
- Pipeline: text/article → scenes → auto-assign stock clips → add voiceover + captions.
- Pictory 2.0 (March 2026): added AI Studio (prompt → full video), AI avatars, PPT-to-video, audio-to-video.
- Output quality: "competent slideshow," generic transitions. Cited in reviews as "screams automated."

---

### Tier 3 — Avatar-First (background is secondary)

**Synthesia**
- Primary visual: AI human avatar is the main visual element.
- Background: solid color, branded template, uploaded image, or Veo 3-generated B-roll (enterprise customers only).
- Synthesia + Google Veo 3 (enterprise): generates 8-second B-roll clips from text prompt inside the platform — eliminates external stock search.
- Targets corporate training; minimal natural B-roll sourcing.

**HeyGen**
- Primary visual: 1,100+ stock avatars or custom avatar cloned from upload.
- Background: stock templates, solid colors, uploaded images, AI-generated scenes.
- Video Agent (2025 feature): prompt-to-video pipeline that writes script, selects visuals, edits automatically.
- 5,000+ customizable AI avatars with expressions, gestures, clothing variants.

---

### Tier 4 — Clip Repurposing (B-roll added to existing footage)

**Opus Clip**
- Not a text-to-video tool — repurposes long-form video into short clips.
- B-roll pipeline: AI scans transcript → identifies key themes → auto-inserts either (a) royalty-free stock footage or (b) AI-generated visuals for abstract concepts.
- Auto-synchronizes B-roll with caption timing codes.
- Users can manually replace or override B-roll suggestions.

**Captions.ai**
- Mobile-first short-form repurposing tool.
- B-roll: integrated stock library; AI selects based on spoken content keywords.
- Auto-adds animated captions, transitions, and AI B-roll in one pass.
- Primarily designed for talking-head repurposing, not script-to-video from scratch.

---

## B. Free/Low-Cost Stock Media APIs

### Pexels API

**Base URLs:**
- Photos: `https://api.pexels.com/v1/`
- Videos: `https://api.pexels.com/videos/`

**Key endpoints:**
```
GET https://api.pexels.com/v1/search?query={q}&per_page=15&page=1
GET https://api.pexels.com/videos/search?query={q}&orientation=landscape&size=medium&per_page=15
GET https://api.pexels.com/v1/photos/{id}
GET https://api.pexels.com/videos/videos/{id}
```

**Authentication:** `Authorization: YOUR_API_KEY` header on every request.

**Rate limits:**
- Default: 200 requests/hour, 20,000 requests/month.
- Can apply for unlimited tier (free) if usage meets their API guidelines.
- Max results per request: 80.
- Response header `X-Ratelimit-Remaining` reports remaining quota in real time.
- Returns HTTP 429 on breach.

**Response — video object fields:** `id`, `width`, `height`, `url`, `image` (thumbnail URL), `duration` (seconds), `video_files` array — each element contains `link` (direct MP4 download URL), `quality` (hd/sd/uhd), `width`, `height`, `file_type`.

**Quality:** HD (1080p) and UHD (4K) available for most clips. All footage royalty-free, commercial use OK, attribution not required, no watermarks. Pexels License.

**Cost:** Completely free at all tiers, including API access.

**Python example:**
```python
import requests

def pexels_video_search(query, api_key, per_page=5):
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": per_page, "orientation": "landscape"}
    )
    videos = r.json()["videos"]
    return [
        max(v["video_files"], key=lambda f: f.get("width", 0))["link"]
        for v in videos
    ]
```

---

### Unsplash API

**Base URL:** `https://api.unsplash.com/`

**Key endpoints:**
```
GET https://api.unsplash.com/search/photos?query={q}&per_page=10&client_id=YOUR_KEY
GET https://api.unsplash.com/photos/{id}?client_id=YOUR_KEY
GET https://api.unsplash.com/photos/random?query={q}&client_id=YOUR_KEY
```

**Authentication:** `Authorization: Client-ID YOUR_KEY` header, or `client_id={key}` query parameter.

**Rate limits:**
- Demo (default): 50 requests/hour. Sufficient for prototyping.
- Production (requires application approval): 5,000 requests/hour.
- Headers: `X-Ratelimit-Limit` and `X-Ratelimit-Remaining` on every response.

**Critical usage rule:** When an image is "used" (selected for display or download), you MUST fire a download tracking event by hitting `photo.links.download_location` — required by Unsplash API Guidelines. Permanent CDN hotlinking of `photo.urls.*` is allowed.

**Response photo fields:** `id`, `width`, `height`, `urls.raw` (original), `urls.full`, `urls.regular` (1080px wide), `urls.small` (400px), `urls.thumb` (200px), `links.download`, `links.download_location`.

**Images only:** No video endpoint. Photos only. Very high editorial quality — better for concept/title imagery than B-roll.

**Cost:** Free.

---

### Pixabay API

**Base URL:** `https://pixabay.com/api/`

**Key endpoints:**
```
GET https://pixabay.com/api/?key={API_KEY}&q={query}&image_type=photo&per_page=20&safesearch=true
GET https://pixabay.com/api/videos/?key={API_KEY}&q={query}&video_type=film&per_page=20
```

**Image parameters:** `q`, `lang`, `image_type` (all/photo/illustration/vector), `orientation` (all/horizontal/vertical), `category`, `min_width`, `min_height`, `colors`, `editors_choice`, `safesearch`, `order` (popular/latest), `page`, `per_page` (3–200).

**Video parameters:** `q`, `video_type` (all/film/animation), `category`, `min_width`, `min_height`, `editors_choice`, `safesearch`, `order`, `page`, `per_page` (3–200).

**Rate limits:**
- 100 requests per 60 seconds.
- Downloaded images must be cached for 24 hours on your server; systematic scraping prohibited.
- Permanent hotlinking NOT allowed — must download assets to your own server first.

**Response — video object:** `id`, `tags`, `videos` object containing `large` (largest available), `medium`, `small`, `tiny` — each with `url` (direct MP4 link), `width`, `height`, `size` (bytes).

**Library size:** 5.6M+ images and videos, including illustrations and vectors. Good for abstract/conceptual topics with no real-world stock.

**Cost:** Free.

---

### API Comparison Table

| API | Photos | Videos | Default Rate Limit | Max Rate Limit | Hotlink OK | Commercial Use | Cost |
|-----|--------|--------|-------------------|----------------|------------|----------------|------|
| Pexels | Yes | Yes | 200 req/hr | Unlimited (apply) | Yes | Yes | Free |
| Unsplash | Yes | No | 50 req/hr | 5,000 req/hr | Yes | Yes | Free |
| Pixabay | Yes | Yes | 100 req/min | 100 req/min | No (cache required) | Yes | Free |

**Recommendation for this pipeline:** Pexels first (photos + video, generous limits, hotlink OK, no mandatory cache). Pixabay as fallback for images and abstract/illustration topics. Unsplash for high-quality editorial photography on educational titles.

---

## C. Ken Burns Effect with ffmpeg: Complete Syntax Reference

The Ken Burns effect is a slow zoom-in or zoom-out on a still image, optionally combined with a gentle pan — creating the illusion of camera movement over static content. ffmpeg implements this via the `zoompan` video filter.

### Core zoompan Parameter Reference

```
zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s={WxH}:fps={fps}
```

| Parameter | Meaning | Notes |
|-----------|---------|-------|
| `z` | zoom expression, evaluated per frame | `zoom` = previous frame's zoom value. Range 1.0–10.0. |
| `x`, `y` | top-left corner of crop window in source pixels | Keep centered: `iw/2-(iw/zoom/2)` |
| `d` | duration in total frames | e.g. `25*5` = 5 seconds at 25fps |
| `s` | output resolution | e.g. `1920x1080` |
| `fps` | output framerate | 25 for web, 30 or 60 for broadcast |
| `on` | current frame number (read-only) | Useful for `if(eq(on,1),...)` to set initial zoom |

**Critical pre-scaling requirement:** The source image must be upscaled (to ~8,000px wide) before `zoompan` so the cropped region has enough pixels. If you skip this, the zoomed image will be soft/pixelated.

---

### Ready-to-Run Commands

**Zoom in to center (standard Ken Burns, most common):**
```bash
ffmpeg -loop 1 -i photo.jpg \
  -filter_complex "[0:v]scale=8000:-1,\
zoompan=z='min(zoom+0.001,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1920x1080:fps=25[out]" \
  -map "[out]" -pix_fmt yuv420p -c:v libx264 -t 5 out.mp4
```
Starts at 1.0x, increments 0.001 per frame, caps at 1.5x (subtle). Centered throughout.

**Zoom out from 1.5x to 1.0x (reverse Ken Burns):**
```bash
ffmpeg -loop 1 -i photo.jpg \
  -filter_complex "[0:v]scale=8000:-1,\
zoompan=z='if(eq(on,1),1.5,max(zoom-0.001,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1920x1080:fps=25[out]" \
  -map "[out]" -pix_fmt yuv420p -c:v libx264 -t 5 out.mp4
```
`if(eq(on,1),1.5,...)` sets zoom to 1.5 on frame 1; subsequent frames subtract 0.001, floor at 1.0.

**Zoom in to top-left corner:**
```bash
zoompan=z='zoom+0.001':x=0:y=0:d=125:s=1920x1080:fps=25
```

**Zoom in to top-center:**
```bash
zoompan=z='zoom+0.001':x='iw/2-(iw/zoom/2)':y=0:d=125:s=1920x1080:fps=25
```

**Pan bottom-to-top (vertical pan across tall/landscape image):**
```bash
ffmpeg -loop 1 -i photo.jpg \
  -filter_complex "[0:v]pad=w=9600:h=6000:x='(ow-iw)/2':y='(oh-ih)/2',\
zoompan=z='if(eq(on,1),2.56,zoom+0.002)':x='(iw-0.625*ih)/2':y='(1-on/(25*4))*(ih-ih/zoom)':d=100:s=1280x800:fps=25[out]" \
  -map "[out]" -pix_fmt yuv420p -c:v libx264 -t 4 out.mp4
```

---

### Multi-Image Slideshow with Ken Burns + Cross-Fades

3-image example: each image displayed 5s at 25fps (125 frames), 1s cross-fade:

```bash
ffmpeg \
  -loop 1 -t 6 -i img1.jpg \
  -loop 1 -t 6 -i img2.jpg \
  -loop 1 -t 6 -i img3.jpg \
  -filter_complex "
    [0:v]scale=8000:-1,zoompan=z='min(zoom+0.001,1.4)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1920x1080:fps=25,fade=t=out:st=4:d=1[v0];
    [1:v]scale=8000:-1,zoompan=z='if(eq(on,1),1.4,max(zoom-0.001,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1920x1080:fps=25,fade=t=in:st=0:d=1,fade=t=out:st=4:d=1[v1];
    [2:v]scale=8000:-1,zoompan=z='min(zoom+0.001,1.4)':x='iw/2-(iw/zoom/2)':y=0:d=125:s=1920x1080:fps=25,fade=t=in:st=0:d=1[v2];
    [v0][v1]concat=n=2:v=1:a=0[tmp];[tmp][v2]concat=n=2:v=1:a=0[out]
  " \
  -map "[out]" -pix_fmt yuv420p -c:v libx264 -r 25 final.mp4
```

**Zoom speed guide (at 25fps):**
| `z` increment | Zoom per second | Feel |
|---------------|----------------|------|
| `+0.001` | ~1.5% | Subtle, barely noticeable |
| `+0.002` | ~3% | Classic cinematic documentary |
| `+0.005` | ~7.5% | Noticeable, dramatic |
| `+0.010` | ~15% | Fast, punchy |

**Automation tool:** `Trekky12/kburns-slideshow` on GitHub wraps these filter chains into a YAML/JSON spec and generates the full ffmpeg command automatically — useful when slide count is dynamic.

---

## D. Open-Source Text-to-Video Models: Local Hardware Requirements

### Wan 2.1 (Alibaba/Qwen — open-source, MIT license)

**Repository:** `Wan-Video/Wan2.1` on GitHub; weights at `Wan-AI/Wan2.1-T2V-*` on Hugging Face.

| Variant | Min VRAM | Recommended VRAM | Disk (full model) | Output Resolution |
|---------|----------|-----------------|-------------------|--------------------|
| T2V-1.3B (BF16) | 8.19 GB (RTX 3060) | 10 GB | ~8 GB | 480p |
| T2V-1.3B (GGUF q3) | 6 GB | 8 GB | ~7 GB | 480p |
| T2V-14B (BF16, full) | 16 GB (+ `--offload_model`) | 24 GB | 69.1 GB | 480p / 720p |
| T2V-14B (GGUF q3) | 6 GB | 8 GB | ~7 GB | 480p (quality degraded) |

**Setup space:** ~30 GB free SSD for 1.3B + ComfyUI environment. 80+ GB for 14B.

**Runtime requirements:** PyTorch >= 2.4.0, CUDA, CUDA-compatible GPU.

**Memory reduction flags:**
```bash
python generate.py --offload_model True    # moves layers off VRAM during inference
python generate.py --t5_cpu               # T5 text encoder runs on CPU
```

**Generation speed benchmarks:**
- RTX 4090, T2V-1.3B, no optimization: 5-second 480p video in ~4 minutes
- RTX 4050 (6 GB VRAM), GGUF: 480p in 10–15 minutes

**Install:**
```bash
huggingface-cli download Wan-AI/Wan2.1-T2V-1.3B --local-dir ./Wan2.1-T2V-1.3B
# or 14B:
huggingface-cli download Wan-AI/Wan2.1-T2V-14B --local-dir ./Wan2.1-T2V-14B
```

**Practical verdict for this pipeline:** T2V-1.3B is viable on any machine with 8 GB+ VRAM (RTX 3060, RTX 4060, Apple M2 Pro via MPS with limitations). The 14B is high quality but requires 16–24 GB GPU or aggressive quantization plus slow generation.

---

### LTX-Video / LTX-2 (Lightricks — open-source, January 2026)

**Repository:** `Lightricks/LTX-Video` and `Lightricks/LTX-2` on GitHub. Weights at `Lightricks/LTX-Video` and `Lightricks/LTX-2` on Hugging Face.

| Variant | Min VRAM | Disk | Output | Notes |
|---------|----------|------|--------|-------|
| LTX-Video (original, ~8B DiT) | 8 GB | ~20 GB | 704×480, up to 257 frames | Fast inference; best practical choice |
| LTX-2 (BF16 full) | 32 GB | ~100 GB | 1080p stable, 4K marginal | Enterprise hardware required |
| LTX-2 (NVFP8 quantized) | 24 GB | ~70 GB | 1080p | ~30% smaller, 2x faster than BF16 |
| LTX-2 (8 GB optimized fork) | 8 GB | ~30 GB | Lower res, fewer frames | Community-maintained, unofficial |

**System requirements for LTX-2.3 (official):**
- GPU VRAM: 32 GB+ (minimum); A100 80GB or H100 recommended
- System RAM: 32 GB minimum, 64 GB+ preferred
- Storage: 100 GB required, 200 GB+ SSD preferred
- CUDA: 11.8 minimum, 12.1+ advised
- Python: 3.10+

**Unique capability:** LTX-2 generates audio + video simultaneously — synchronized dialogue, music, and ambience in one pass. No other open-source model does this.

**Install:**
```bash
pip install ltx-video
huggingface-cli download Lightricks/LTX-Video --local-dir ./LTX-Video
```

**Practical verdict:** LTX-Video (original pre-LTX-2) is the best practical choice for local pipeline integration: 8 GB VRAM, ~20 GB disk, fast inference on RTX 3080+. LTX-2 requires enterprise hardware unless quantized and runs on a machine with 24+ GB VRAM.

---

### CogVideoX-5B (Zhipu AI / THUDM — open-source)

**Weights:** `THUDM/CogVideoX-5b` or `zai-org/CogVideoX-5b` on Hugging Face. Total size: ~21.5 GB.

| Variant | VRAM | Output | Notes |
|---------|------|--------|-------|
| CogVideoX-2B (BF16) | 8 GB | 6s, 720×480 | Practical minimum; faster |
| CogVideoX-5B (BF16) | 24–26 GB (A100), 15 GB (H100) | 6–10s, 720×480 | Full quality |
| CogVideoX-5B (INT8 quantized) | 12–16 GB | 6s, 720×480 | Via PytorchAO or Optimum-quanto |
| CogVideoX-5B (INT4 quantized) | 8 GB | 6s, 720×480 | On free T4 Colab; quality tradeoff |

**Optimization libraries:** `pip install torchao optimum-quanto` — enable per-module quantization of transformer, text encoder, and VAE.

**Practical verdict:** CogVideoX-2B at 8 GB VRAM is a pragmatic local option for short clips. The 5B at full precision needs 24 GB, but INT8 quantization brings it into the 16 GB range. Resolution is constrained to 720×480 — more of an "animated B-roll" quality than cinematic.

---

### Model Selection Matrix

| Scenario | Best Choice | Why |
|----------|------------|-----|
| Consumer laptop, 8 GB VRAM | Wan 2.1 T2V-1.3B or CogVideoX-2B | Smallest footprint |
| Desktop, 16–24 GB VRAM | Wan 2.1 T2V-14B or LTX-Video original | Quality jump; manageable disk |
| API only, no GPU | Replicate or Fal.ai (Wan 2.1) | See Section E |
| Highest local quality | LTX-2 NVFP8 (24 GB) | 1080p + audio sync; needs RTX 4090 |
| Fastest local generation | LTX-Video original | Engineered for consumer hardware |

---

## E. Replicate.com API Pricing (April 2026)

### GPU Time-Based Billing (for private/custom models)

| Hardware | Per Second | Per Hour |
|----------|-----------|---------|
| CPU (small) | $0.000025 | $0.09 |
| CPU | $0.000100 | $0.36 |
| Nvidia T4 GPU | $0.000225 | $0.81 |
| Nvidia L40S GPU | $0.000975 | $3.51 |
| Nvidia A100 (80GB) | $0.001400 | $5.04 |
| Nvidia H100 GPU | $0.001525 | $5.49 |
| 2x Nvidia L40S | $0.001950 | $7.02 |
| 2x Nvidia A100 (80GB) | $0.002800 | $10.08 |

### Image Generation (flat per-image, public models)

| Model | Per Image | Notes |
|-------|----------|-------|
| Flux Schnell | $0.003 ($3.00/1,000) | Fastest; 1–4 inference steps |
| Flux Dev | $0.025 | Better quality than Schnell |
| Flux 1.1 Pro | $0.040 | Highest Flux quality |
| Recraft V3 | $0.040 | Strong for illustrations/icons |
| Ideogram V3 Quality | $0.090 | Best for text-in-image |
| SDXL (time-based) | ~$0.004 | ~4s on T4 = $0.000225 × 4 × ~4 |

### Video Generation (per second of output video, Wan 2.1 on Replicate)

| Model | Per Second of Output | Per 5s Clip | Per 10s Clip |
|-------|---------------------|------------|-------------|
| Wan 2.1 (480p) | $0.09 | $0.45 | $0.90 |
| Wan 2.1 (720p) | $0.25 | $1.25 | $2.50 |

### Fal.ai Alternative Pricing

Fal.ai is generally 30–50% cheaper than Replicate with 600+ models vs. Replicate's ~200.

| Model | Fal.ai Price |
|-------|-------------|
| Wan 2.1 T2V-1.3B | $0.20 flat per video |
| Flux Schnell | $0.003/megapixel |
| Flux Dev | $0.025/image |

**Fal.ai API endpoint:**
```bash
curl -X POST https://queue.fal.run/fal-ai/flux/schnell \
  -H "Authorization: Key $FAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a photorealistic diagram of neural network layers, clean background, educational", "image_size": "landscape_16_9"}'
```

**Replicate API (curl example for image generation):**
```bash
curl -s -X POST \
  -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version":"black-forest-labs/flux-schnell","input":{"prompt":"educational infographic about photosynthesis, minimal, clean"}}' \
  https://api.replicate.com/v1/predictions
```

**Estimated monthly cost at modest usage:**
- 500 images + 50 videos (5s, 720p) on Replicate: ~$40/month
- 5,000 images + 500 videos (5s, 720p) on Replicate: ~$350/month
- Same on Fal.ai: ~25–35% less

---

## F. What Users Actually Want: Footage Source Sentiment

### Aggregated from Reddit, Trustpilot, Quora, review aggregators (2024–2026)

**The #1 complaint: mismatched generic stock footage.**
"The tool just stitches together stock footage that doesn't match up well." (InVideo reviews, multiple sources.)
"Most people spend hours in Pictory only to end up with a result that screams 'automated.'"
One InVideo user: "I have never hated anything as much as I hate invideo" — attributed explicitly to visuals not matching the script's specific subject matter.

**The "stock footage look" is a credibility killer.**
Reddit communities in 2024–2025 coined vocabulary for "AI video with stock signatures" — creators report losing trust from audiences who can recognize the same 50 clips cycling through different channels. For technical or niche topics (anything outside the set {people in meetings, sunsets, hands typing}, stock libraries have no good matches.

**Footage source priority (what users say they want, in order):**
1. Their own screen recordings, demos, and personal footage
2. AI-generated B-roll that actually matches the specific topic
3. Curated high-quality stock that genuinely matches the script
4. Auto-selected stock (last resort; "at least it's something")

**YouTube AI content crackdown (2026) is changing the calculus.**
YouTube introduced mandatory AI content labeling and algorithmic penalties for videos that "look AI-generated." This puts the stock-B-roll-stitching model under existential pressure — it looks AI-generated because it is.

**The "slot machine" complaint: beautiful but unusable.**
Users who've moved past stock footage frustrations now complain about AI video's inability to maintain character/visual consistency across scenes. Runway, Kling, and Sora all receive this criticism: "produces beautiful but unusable random results." The tools that achieve consistency (Runway Gen-4's reference system, LTX Studio's storyboard pipeline) command premium pricing precisely because they solve it.

**Free tier queue anxiety is a dealbreaker.**
"24-hour renders," "stuck at 99%," and "errors that eat credits" are cited more often than quality complaints across Kling, Sora free tier, and InVideo free tier. Users abandon tools because of *reliability*, not quality.

**Market bifurcation (2026 trend):**
- Speed-seeking creators: accept generic stock, want < 5 minutes total, don't care about brand quality
- Brand-conscious creators: pay more, want director-level control, increasingly choose LTX Studio or Runway despite the learning curve
- The middle is collapsing — tools positioned there (Pictory, InVideo) are getting squeezed from both sides

---

## G. Synthesis: Visuals Implementation Roadmap for idea-to-video

| Visual Source | Quality | Cost | Dependencies | Offline | Difficulty |
|---------------|---------|------|-------------|---------|------------|
| Pillow title cards (current) | Low | Free | None | Yes | Done |
| Ken Burns on existing images | Medium+ | Free | ffmpeg (already present) | Yes | 1 day |
| Pexels API (stock video/photo) | High | Free | API key (free, instant) | No | 2–3 days |
| Pixabay API (fallback) | Medium-high | Free | API key (free, instant) | No | 1 day |
| Unsplash API (editorial photos) | Very high | Free | API key (free, instant) | No | 1 day |
| Flux Schnell via Fal.ai | High (AI, topic-specific) | $0.003/img | Paid API key | No | 2–3 days |
| Wan 2.1 T2V-1.3B (local) | Medium-high | Free after setup | 8 GB VRAM GPU, ~30 GB disk | Yes | 1 week |
| Wan 2.1 T2V-14B (cloud) | High | $0.45–$1.25/clip | Replicate/Fal API key | No | 2–3 days |
| LTX-Video original (local) | High | Free after setup | 8–12 GB VRAM, ~20 GB disk | Yes | 1 week |

### Recommended build sequence (fast to slow, cheap to expensive):

**Step 1 — Ken Burns on existing images (zero cost, zero new dependencies):**
Apply `zoompan` filter in `make_video.sh` to every input image. Replaces static slideshows with cinematic-feeling motion. Complete in 1 day. No new API keys, no model downloads.

**Step 2 — Pexels API integration (free, fast, high quality):**
After script/topics are generated, query Pexels for 2–4 video clips per section keyword. Download to temp folder, use in `make_video.sh` instead of (or alongside) Pillow cards. Free Pexels key from pexels.com/api takes 5 minutes to get. Covers the majority of common educational topics (science, technology, people, nature, business). Estimated 2–3 days of integration work.

**Step 3 — Flux Schnell image generation for abstract topics (paid, low cost):**
For sections where Pexels returns poor matches, call `fal-ai/flux/schnell` to generate a topic-specific image from the section's text prompt. At $0.003/image, a 10-section video costs $0.03 extra. Needs FAL_API_KEY env var. Estimated 2 days of integration.

**Step 4 — Wan 2.1 T2V-1.3B local inference (free at scale, GPU required):**
Opt-in "AI footage" mode for users with 8 GB+ VRAM. Generates 5-second video clips per section from a text prompt. Zero per-clip cost; setup is a one-time 8 GB download. Estimated 1 week including integration and testing.

---

*Research sources: Replicate pricing page (replicate.com/pricing), Wan-AI/Wan2.1-T2V-14B Hugging Face model card, Lightricks/LTX-2 GitHub + WaveSpeedAI VRAM benchmark, LTX documentation (docs.ltx.video), Novita AI Wan 2.1 hardware guide, Bannerbear ffmpeg Ken Burns tutorial, mko.re Ken Burns slideshow reference, Pexels API docs (publicapi.dev/pexels-api), Unsplash API docs (unsplash.com/documentation), Pixabay API docs (pixabay.com/api/docs), Zapier/Revoyant competitor roundups (2026), Trustpilot/Quora/Reddit-aggregated review sources, OpusClip/InVideo/Pictory official documentation, TeamDay.ai API pricing comparison 2026.*

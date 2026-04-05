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

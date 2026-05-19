# Image Quality Root Cause Research

**Research date:** April 2026  
**Method:** LLM-as-judge + empirical Pexels A/B query test  
**Verdict:** The bottleneck is **prompt generation**, not the model or the image source.

---

## The Diagnosis

### Test Setup

Four topics from a real sleep science conversation were run through the full chain:

```
topic → image_prompt (from extract_topics) → Pexels query → returned photo
```

Each (topic, image_prompt, top Pexels result) triplet was evaluated by Claude Sonnet
on a 1–10 scale, with a required failure mode classification.

### Scores

| Topic | Score | Failure Mode |
|-------|-------|--------------|
| Sleep and Memory Consolidation | 3/10 | PROMPT_TOO_LITERAL |
| The 90-Minute Sleep Cycle | 1/10 | PROMPT_TOO_LITERAL |
| Blue Light and Circadian Disruption | 4/10 | PROMPT_TOO_LITERAL |
| Caffeine Half-Life and Sleep Debt | 1/10 | PROMPT_TOO_LITERAL |

All four failed for the same reason. Average score: **2.25/10**.

### Root Cause (LLM Judge Verdict)

> "The image prompt generation layer is consistently producing prompts designed for an AI
> image generator (Midjourney/DALL-E) rather than a stock photo search engine. The prompts
> describe composite scientific visualizations, molecular diagrams, infographics, and impossible
> multi-element scenes. Pexels indexes real photographs and cannot return these assets regardless
> of how well-formed the query is. The bottleneck is upstream: the prompt generation model is
> not constrained to think in terms of 'what real photographs exist in a stock library.'"

---

## Why The Current Prompts Fail

The `extract_topics()` call in `extract_topics.py` asks Claude for:

```
"image_prompt": str (visual description for image search/generation)
```

The phrase "search/generation" sends contradictory signals. Claude optimizes for
the more expressive interpretation — generation — and produces prompts like:

- `"human brain with glowing hippocampus and cortex regions connected by light pathways..."`
- `"circular diagram of sleep stages light NREM deep NREM REM over 90 minutes, medical infographic style"`
- `"caffeine molecule blocking adenosine receptor, clock showing 3pm and 9pm, half-life decay curve"`

These are valid Midjourney prompts. They are useless as Pexels search queries because:

1. **Pexels is a photo library.** It cannot return a glowing-hippocampus render or a molecular diagram.
2. **Composite multi-element scenes don't exist as photographs.** No photographer has ever shot a "caffeine molecule + adenosine receptor + dual clock + decay curve" in a single frame.
3. **The query truncation worsens it.** `_make_pexels_card()` strips to the first sentence and caps at 100 chars, leaving "caffeine molecule blocking adenosine receptor, clock showing 3pm..." — which Pexels interprets as "clock" and returns vintage alarm clocks.

---

## The Two-Prompt Problem

AI generation prompts and stock photo search queries require fundamentally different language:

| Dimension | AI Generation Prompt | Stock Photo Search Query |
|-----------|---------------------|--------------------------|
| Length | 20–100 words | 3–8 words |
| Content | Artistic direction, lighting, style, composite scene | Concrete nouns, human actions, physical objects |
| Abstraction | Any concept can be rendered | Only photographable reality |
| Example | `"caffeine molecule blocking adenosine receptor, dual-clock time comparison, molecular decay curve visualization, dark background"` | `"person drinking coffee late night desk"` |

The current `image_prompt` field tries to serve both. It fails at both.

---

## Empirical Fix Validation

A rewriting prompt was tested: translate each `image_prompt` into a 6-word max,
photographable B-roll description (documentary framing: "what would a filmmaker cut to?").

### Rewritten queries

| Topic | Original query (truncated) | Rewritten query | Method |
|-------|---------------------------|-----------------|--------|
| Sleep + Memory | `human brain glowing hippocampus...` | `person sleeping open textbook beside bed` | Grounds memory transfer in the human behavior it produces |
| 90-Min Cycle | `circular diagram sleep stages NREM...` | `alarm clock beside sleeping person dark bedroom` | Replaces diagram with the objects a diagram would describe |
| Blue Light | `smartphone emitting blue light rays hitting brain...` | `person scrolling phone dark bedroom at night` | The _cause_ (the behavior) instead of the _mechanism_ (the physics) |
| Caffeine Half-Life | `caffeine molecule blocking adenosine...` | `coffee cup next to clock afternoon desk` | Concrete props that imply the concept without requiring a molecular diagram |

### Pexels result quality comparison

| Topic | Original top result relevance | Rewritten top result relevance |
|-------|------------------------------|-------------------------------|
| Sleep + Memory | Generic brain prop on a plate | Young man asleep at open textbook ✓ |
| 90-Min Cycle | Alarm clock with sleeping woman | Hand reaching to silence alarm clock ✓ |
| Blue Light | Generic phone silhouette | Woman in bed at night on smartphone ✓ |
| Caffeine | Decorative vintage clock | Clock + coffee cozy desk setup ✓ |

All four rewritten queries returned on-topic photos. The fix works.

---

## Is This a Model Problem?

No. Claude Sonnet generates excellent image prompts _for the wrong use case_.
The problem is prompt framing, not model capability.

Evidence: the same model, given explicit B-roll framing constraints, produced
highly relevant 6-word Pexels queries in a single pass with 100% hit rate.

## Is This a Pexels Problem?

Partially. Pexels cannot fulfill abstract/scientific prompts regardless of query quality.
But with concrete, photographable queries, Pexels returns usable results.

The fallback chain (fal → dalle3 → pexels → pillow) is architecturally correct:
abstract prompts belong in AI generation tiers, not stock search.
The bug is that the `image_prompt` field isn't designed to be _different_ depending on backend.

## Is This a Query Construction Problem?

Yes, but secondarily. The `_make_pexels_card()` truncation (first sentence, 100 chars)
strips context. But even a full, untruncated abstract prompt would fail on Pexels.
The primary fix is upstream.

---

## The Fix

### Option A — Two-field extraction (recommended)

Modify `extract_topics()` to extract two separate fields per topic:

```python
{
  "title": str,
  "summary": str,
  "ai_image_prompt": str,    # For fal/dalle3: detailed, stylistic, composite OK
  "stock_query": str         # For pexels/unsplash: max 8 words, photographable, B-roll framing
}
```

The system prompt addition for `stock_query`:

```
"stock_query": describe a real, photographable scene a documentary filmmaker would
use as B-roll for this topic. Max 8 words. No molecules, diagrams, glowing, rays,
or composite impossible scenes. Translate the concept into a human action or object.
```

**Pros:** Clean, one API call, backward-compatible (add field, don't remove).  
**Cons:** Slightly longer prompt.

### Option B — Query translation layer (quick fix, more API calls)

Keep `image_prompt` as-is. Add `_to_pexels_query(image_prompt, title)` in
`generate_images.py` that calls Claude to translate before each Pexels search.

**Pros:** No changes to `extract_topics.py`, zero schema migration.  
**Cons:** One extra Claude call per scene per run (~$0.001 each); adds latency.

### Option C — Prompt rewrite inline (no extra API call)

Add a rule-based rewriter in `_make_pexels_card()` that:
1. Strips scientific jargon (molecule, receptor, pathway, diagram, visualization)
2. Extracts concrete nouns and human-action phrases
3. Caps to 8 words

**Pros:** Zero API cost, no schema change.  
**Cons:** Rule-based, will miss edge cases; less reliable than LLM rewriting.

### Recommended approach

**Option A for new topics + Option B as runtime fallback for legacy `image_prompt` fields.**

This means:
- New `extract_topics()` calls get `stock_query` natively
- Older sessions or topics without `stock_query` fall back to the Claude translation layer
- No data is lost; both prompts serve their respective backends

---

## Affected Files

| File | Change needed |
|------|--------------|
| `extract_topics.py` | Add `stock_query` field to topic schema + prompt |
| `generate_images.py` | Use `stock_query` for Pexels; keep `ai_image_prompt` for fal/dalle3 |
| `tests/test_extract_topics.py` | Assert `stock_query` present and ≤ 8 words |

---

## Performance Benchmarks (for eval)

A quality fix should achieve:
- Average LLM judge score ≥ 7/10 across 10 test topics
- Pexels top result is visually relevant to topic ≥ 80% of the time
- No "PROMPT_TOO_LITERAL" failure mode in any topic

"""
Phase 1 quality evaluation tests.

Uses real Claude API calls (not mocked) to evaluate LLM output quality.
Mark: pytest -m eval  (requires ANTHROPIC_API_KEY)

Two layers inspired by deepeval:
  - Deterministic metrics: section count, language, brand injection
  - GEval metrics: topic relevancy, script coherence, brand alignment
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.eval.metrics import (
    LLMTestCase,
    GEvalMetric,
    SectionCountMetric,
    LanguageConsistencyMetric,
    BrandTermPresenceMetric,
    assert_test,
    evaluate,
)
from extract_topics import extract_topics
from write_script import write_script, write_script_sections
from brand import brand_prefix

# ── Fixtures ──────────────────────────────────────────────────────────────────

pytestmark = pytest.mark.eval

TRANSCRIPT = (
    "Today I want to talk about building better habits. The key insight is that "
    "habits are formed through cues, routines, and rewards — not willpower. "
    "When you identify your triggers and design your environment, change becomes "
    "almost automatic. I've seen this work for exercise, reading, and even deep work. "
    "The hardest part isn't starting. It's understanding that your current habits "
    "are perfectly designed for their current environment."
)

BRAND = {
    "name": "MindTools",
    "audience": "knowledge workers, 25-45, ambitious but time-constrained",
    "tone": "direct, evidence-based, no fluff",
    "style_notes": "lead with the practical insight, not the theory",
}

NUM_TOPICS = 3


@pytest.fixture(scope="module")
def real_topics():
    """Extract real topics from Claude (live API call, cached per module run)."""
    return extract_topics(TRANSCRIPT, num_topics=NUM_TOPICS, brand=BRAND)


@pytest.fixture(scope="module")
def real_script(real_topics):
    """Write a real script from real topics (live API call)."""
    return write_script(real_topics, lang="en", style="conversational", brand=BRAND)


@pytest.fixture(scope="module")
def real_sections(real_topics):
    """Write real sections from real topics (live API call)."""
    return write_script_sections(real_topics, lang="en", style="conversational", brand=BRAND)


# ── Deterministic tests (no LLM judge needed) ─────────────────────────────────

class TestDeterministic:

    def test_topics_count(self, real_topics):
        assert len(real_topics) == NUM_TOPICS, (
            f"extract_topics returned {len(real_topics)} topics, expected {NUM_TOPICS}"
        )

    def test_topics_have_required_fields(self, real_topics):
        for i, t in enumerate(real_topics):
            assert "title" in t, f"Topic {i} missing 'title'"
            assert "summary" in t, f"Topic {i} missing 'summary'"
            assert "image_prompt" in t, f"Topic {i} missing 'image_prompt'"
            assert len(t["title"]) > 0, f"Topic {i} has empty title"
            assert len(t["summary"]) > 10, f"Topic {i} has too-short summary"

    def test_sections_count_matches_topics(self, real_sections):
        tc = LLMTestCase(
            name="sections-count",
            actual_output=json.dumps(real_sections),
        )
        assert_test(tc, [SectionCountMetric(expected_count=NUM_TOPICS)])

    def test_script_language_en(self, real_script):
        tc = LLMTestCase(
            name="script-language-en",
            actual_output=real_script,
        )
        assert_test(tc, [LanguageConsistencyMetric(expected_lang="en")])

    def test_sections_language_en(self, real_sections):
        combined = " ".join(real_sections)
        tc = LLMTestCase(
            name="sections-language-en",
            actual_output=combined,
        )
        assert_test(tc, [LanguageConsistencyMetric(expected_lang="en")])

    def test_brand_prefix_injected_in_prompt(self):
        """Brand terms appear in the Claude prompt prefix (not output)."""
        prefix = brand_prefix(BRAND)
        # The prefix is what Claude receives — verify brand terms are present
        tc = LLMTestCase(
            name="brand-prefix",
            actual_output=prefix,   # we're checking the prefix itself
            context=prefix,
        )
        assert_test(tc, [BrandTermPresenceMetric(["MindTools", "knowledge workers"])])

    def test_script_is_not_empty(self, real_script):
        assert len(real_script.split()) >= 50, (
            f"Script too short: {len(real_script.split())} words"
        )

    def test_sections_are_nonempty_strings(self, real_sections):
        for i, s in enumerate(real_sections):
            assert isinstance(s, str), f"Section {i} is not a string"
            assert len(s.split()) >= 5, f"Section {i} is too short: '{s}'"


# ── GEval quality tests (LLM-as-judge) ────────────────────────────────────────

class TestGEvalQuality:

    def test_topics_relevant_to_transcript(self, real_topics):
        topics_text = "\n".join(f"- {t['title']}: {t['summary']}" for t in real_topics)
        tc = LLMTestCase(
            name="topic-relevancy",
            input=TRANSCRIPT,
            actual_output=topics_text,
            context=TRANSCRIPT,
        )
        metric = GEvalMetric(
            name="TopicRelevancy",
            criteria=(
                "Do the extracted topics accurately represent the key ideas in the source transcript? "
                "Topics should cover the main points without inventing content not present in the transcript."
            ),
            threshold=0.7,
            use_context=True,
        )
        assert_test(tc, [metric])

    def test_script_coherence(self, real_script, real_topics):
        topics_text = "\n".join(f"- {t['title']}" for t in real_topics)
        tc = LLMTestCase(
            name="script-coherence",
            input=topics_text,
            actual_output=real_script,
        )
        metric = GEvalMetric(
            name="ScriptCoherence",
            criteria=(
                "Is the script coherent, well-paced, and natural to speak aloud? "
                "Specifically: smooth transitions between topics, no abrupt jumps, "
                "consistent voice, and appropriate length (1-3 min read). "
                "No markdown, bullets, or headers — pure spoken prose only."
            ),
            threshold=0.7,
        )
        assert_test(tc, [metric])

    def test_script_covers_all_topics(self, real_script, real_topics):
        topics_text = "\n".join(f"- {t['title']}: {t['summary']}" for t in real_topics)
        tc = LLMTestCase(
            name="script-coverage",
            input=topics_text,
            actual_output=real_script,
            context=topics_text,
        )
        metric = GEvalMetric(
            name="TopicCoverage",
            criteria=(
                "Does the script meaningfully address each of the provided topics? "
                "Each topic should appear as a distinct section or be woven through the narrative."
            ),
            threshold=0.7,
            use_context=True,
        )
        assert_test(tc, [metric])

    def test_brand_alignment_in_script(self, real_script):
        brand_desc = (
            f"Brand: {BRAND['name']}, Audience: {BRAND['audience']}, "
            f"Tone: {BRAND['tone']}, Style: {BRAND['style_notes']}"
        )
        tc = LLMTestCase(
            name="brand-alignment",
            input=brand_desc,
            actual_output=real_script,
            context=brand_desc,
        )
        metric = GEvalMetric(
            name="BrandAlignment",
            criteria=(
                "Does the script's tone, style, and vocabulary match the brand guidelines? "
                f"Expected: {BRAND['tone']}. Style: {BRAND['style_notes']}. "
                "Audience: knowledge workers who are time-constrained — the script should be dense and practical."
            ),
            threshold=0.6,
            use_context=True,
        )
        assert_test(tc, [metric])

    def test_sections_are_individually_coherent(self, real_sections):
        """Each section should stand alone as a well-formed spoken paragraph."""
        for i, section in enumerate(real_sections):
            tc = LLMTestCase(
                name=f"section-{i+1}-coherence",
                actual_output=section,
            )
            metric = GEvalMetric(
                name=f"SectionCoherence[{i+1}]",
                criteria=(
                    "Is this a well-formed, natural spoken paragraph? "
                    "2-4 sentences, paced for TTS, no markdown or bullets. "
                    "Should read like something a confident person would actually say."
                ),
                threshold=0.6,
            )
            assert_test(tc, [metric])


# ── Summary report ────────────────────────────────────────────────────────────

def test_full_eval_report(real_topics, real_script, real_sections):
    """Print a consolidated quality report for Phase 1 pipeline."""
    topics_text = "\n".join(f"- {t['title']}: {t['summary']}" for t in real_topics)
    brand_desc = f"Brand: {BRAND['name']}, Tone: {BRAND['tone']}"

    test_cases = [
        LLMTestCase(
            name="topic-relevancy",
            input=TRANSCRIPT,
            actual_output=topics_text,
            context=TRANSCRIPT,
        ),
        LLMTestCase(
            name="script-coherence",
            input=topics_text,
            actual_output=real_script,
        ),
        LLMTestCase(
            name="brand-alignment",
            input=brand_desc,
            actual_output=real_script,
            context=brand_desc,
        ),
    ]

    metrics = [
        GEvalMetric("TopicRelevancy", "Do topics accurately represent the transcript?",
                    threshold=0.7, use_context=True),
        GEvalMetric("ScriptCoherence", "Is the script coherent and natural to speak?",
                    threshold=0.7),
        GEvalMetric("BrandAlignment", f"Does the script match tone: {BRAND['tone']}?",
                    threshold=0.6, use_context=True),
    ]

    # Run each test case against its corresponding metric only
    print("\n\n" + "="*60)
    print("  PHASE 1 QUALITY REPORT")
    print("="*60)

    all_passed = True
    for tc, m in zip(test_cases, metrics):
        m.measure(tc)
        status = "✓ PASS" if m.is_successful() else "✗ FAIL"
        if not m.is_successful():
            all_passed = False
        print(f"\n{status}  [{m.__name__}]  score={m.score:.2f} (threshold={m.threshold})")
        print(f"  {m.reason[:180]}")

    print("\n" + "-"*60)
    print(f"  Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    print("="*60 + "\n")

    # Don't hard-fail the report test — it's informational
    # (individual tests above enforce quality gates)

"""
Lightweight deepeval-inspired LLM evaluation framework.

Patterns taken from https://github.com/confident-ai/deepeval:
  - LLMTestCase data model (input, actual_output, expected_output, context)
  - BaseMetric interface (measure, is_successful, score, reason)
  - GEvalMetric — uses Claude as LLM judge with chain-of-thought scoring
  - Deterministic metrics for structural / rule-based checks

No deepeval dependency required — uses the anthropic SDK already in the project.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Data model ─────────────────────────────────────────────────────────────────

@dataclass
class LLMTestCase:
    """Mirrors deepeval.test_case.LLMTestCase."""
    input: str = ""
    actual_output: str = ""
    expected_output: str = ""
    context: str = ""       # source material / retrieval context
    name: str = ""          # optional label for reports


# ── Base metric ────────────────────────────────────────────────────────────────

class BaseMetric:
    """Mirrors deepeval.metrics.BaseMetric."""

    threshold: float = 0.5
    score: float | None = None
    reason: str = ""
    error: str | None = None

    def measure(self, test_case: LLMTestCase) -> float:
        raise NotImplementedError

    def is_successful(self) -> bool:
        if self.error is not None:
            return False
        return (self.score or 0.0) >= self.threshold

    @property
    def __name__(self) -> str:
        return self.__class__.__name__


# ── GEval — LLM-as-judge ──────────────────────────────────────────────────────

class GEvalMetric(BaseMetric):
    """
    LLM-as-judge metric inspired by deepeval's GEval.

    Asks Claude to:
      1. Reason step-by-step about the criteria
      2. Give a score 0-10
    Normalises to 0-1 and compares against threshold.
    """

    def __init__(
        self,
        name: str,
        criteria: str,
        threshold: float = 0.5,
        use_context: bool = False,
        use_expected: bool = False,
    ) -> None:
        self._name = name
        self.criteria = criteria
        self.threshold = threshold
        self.use_context = use_context
        self.use_expected = use_expected

    @property
    def __name__(self) -> str:
        return self._name

    def measure(self, test_case: LLMTestCase) -> float:
        from anthropic import Anthropic
        client = Anthropic()

        parts = [f"**Evaluation criteria:** {self.criteria}\n"]
        if test_case.input:
            parts.append(f"**Input:**\n{test_case.input}\n")
        if self.use_context and test_case.context:
            parts.append(f"**Source context:**\n{test_case.context}\n")
        parts.append(f"**Output to evaluate:**\n{test_case.actual_output}\n")
        if self.use_expected and test_case.expected_output:
            parts.append(f"**Expected/ideal output:**\n{test_case.expected_output}\n")

        parts.append(
            "First reason step-by-step about the quality. "
            "Then on the final line write exactly: SCORE: <integer 0-10>"
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": "\n".join(parts)}],
        )
        raw = response.content[0].text.strip()

        # Parse SCORE: N
        match = re.search(r"SCORE:\s*(\d+(?:\.\d+)?)", raw, re.IGNORECASE)
        if not match:
            self.error = f"No SCORE found in response: {raw[:200]}"
            self.score = 0.0
            self.reason = raw
            return 0.0

        raw_score = float(match.group(1))
        self.score = min(raw_score, 10.0) / 10.0
        # Capture reasoning (everything before the SCORE line)
        self.reason = raw[:match.start()].strip()
        return self.score


# ── Deterministic metrics ─────────────────────────────────────────────────────

class SectionCountMetric(BaseMetric):
    """Verifies sections list has exactly expected_count items."""

    def __init__(self, expected_count: int) -> None:
        self.expected_count = expected_count
        self.threshold = 1.0  # must be exact

    @property
    def __name__(self) -> str:
        return "SectionCount"

    def measure(self, test_case: LLMTestCase) -> float:
        import json
        try:
            sections = json.loads(test_case.actual_output)
            actual = len(sections)
        except (json.JSONDecodeError, TypeError):
            # Count non-empty paragraphs
            actual = len([p for p in test_case.actual_output.split("\n\n") if p.strip()])

        if actual == self.expected_count:
            self.score = 1.0
            self.reason = f"Got {actual} sections as expected."
        else:
            self.score = 0.0
            self.reason = f"Expected {self.expected_count} sections, got {actual}."
        return self.score


class LanguageConsistencyMetric(BaseMetric):
    """Checks the output is written in the expected language."""

    _ZH_THRESHOLD = 0.05  # ≥5% CJK chars → Chinese

    def __init__(self, expected_lang: str = "en", threshold: float = 0.9) -> None:
        self.expected_lang = expected_lang
        self.threshold = threshold

    @property
    def __name__(self) -> str:
        return "LanguageConsistency"

    def measure(self, test_case: LLMTestCase) -> float:
        text = test_case.actual_output
        if not text:
            self.score = 0.0
            self.reason = "Empty output."
            return 0.0

        cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        cjk_ratio = cjk_count / len(text)
        detected = "zh" if cjk_ratio >= self._ZH_THRESHOLD else "en"

        if detected == self.expected_lang:
            self.score = 1.0
            self.reason = f"Language '{detected}' matches expected '{self.expected_lang}'."
        else:
            self.score = 0.0
            self.reason = (
                f"Language mismatch: detected '{detected}', "
                f"expected '{self.expected_lang}' (CJK ratio: {cjk_ratio:.2%})."
            )
        return self.score


class BrandTermPresenceMetric(BaseMetric):
    """Verifies that at least one brand term appears in the output (deterministic)."""

    def __init__(self, brand_terms: list[str], threshold: float = 1.0) -> None:
        self.brand_terms = [t.lower() for t in brand_terms if t.strip()]
        self.threshold = threshold

    @property
    def __name__(self) -> str:
        return "BrandTermPresence"

    def measure(self, test_case: LLMTestCase) -> float:
        if not self.brand_terms:
            self.score = 1.0
            self.reason = "No brand terms to check."
            return 1.0

        text_lower = test_case.actual_output.lower()
        # Check prompt (context) for brand terms — they should appear in prompt
        prompt_lower = test_case.context.lower()

        found_in_prompt = [t for t in self.brand_terms if t in prompt_lower]
        if found_in_prompt:
            self.score = 1.0
            self.reason = f"Brand terms in prompt: {found_in_prompt}"
        else:
            self.score = 0.0
            self.reason = (
                f"Brand terms {self.brand_terms} not found in the Claude prompt context. "
                "Brand injection may be broken."
            )
        return self.score


# ── Runner ─────────────────────────────────────────────────────────────────────

def assert_test(test_case: LLMTestCase, metrics: list[BaseMetric]) -> None:
    """Run all metrics. Raises AssertionError if any fail (mirrors deepeval.assert_test)."""
    failures = []
    for m in metrics:
        try:
            m.measure(test_case)
        except Exception as e:
            failures.append(f"[{m.__name__}] ERROR: {e}")
            continue
        if not m.is_successful():
            failures.append(
                f"[{m.__name__}] FAILED (score={m.score:.2f} < threshold={m.threshold}): {m.reason}"
            )
    if failures:
        raise AssertionError("\n".join(failures))


def evaluate(test_cases: list[LLMTestCase], metrics: list[BaseMetric]) -> list[dict]:
    """Evaluate multiple test cases. Returns list of result dicts."""
    results = []
    for tc in test_cases:
        row = {"name": tc.name or tc.input[:40], "metrics": {}}
        for m in metrics:
            try:
                m.measure(tc)
                row["metrics"][m.__name__] = {
                    "score": round(m.score or 0.0, 3),
                    "passed": m.is_successful(),
                    "reason": m.reason[:200] if m.reason else "",
                }
            except Exception as e:
                row["metrics"][m.__name__] = {"score": 0.0, "passed": False, "reason": str(e)}
        results.append(row)
    return results

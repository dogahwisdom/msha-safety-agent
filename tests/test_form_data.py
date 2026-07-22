"""Tests for human-eval form data loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.human_eval.form_data import (
    GENERATED_DIR,
    group_blocks_by_question,
    load_participant_blocks,
)


def test_p001_has_36_blocks_and_12_questions() -> None:
    if not (GENERATED_DIR / "response_templates" / "P001_responses.csv").exists():
        pytest.skip("Generated human-eval packets not present")
    blocks = load_participant_blocks("P001")
    sections = group_blocks_by_question(blocks)
    assert len(blocks) == 36
    assert len(sections) == 12
    assert all(len(section.answers) == 3 for section in sections)


def test_stimulus_ids_match_template_order() -> None:
    if not (GENERATED_DIR / "response_templates" / "P001_responses.csv").exists():
        pytest.skip("Generated human-eval packets not present")
    blocks = load_participant_blocks("P001")
    assert blocks[0].stimulus_id.startswith("S")
    assert blocks[0].system_blinded_label in {"A", "B", "C"}
    assert blocks[0].question_id.split("-", 1)[0] in {"TRD", "CASE", "CLS"}


def test_format_answer_for_display_handles_empty() -> None:
    from eval.human_eval.form_data import EMPTY_ANSWER_PLACEHOLDER, format_answer_for_display

    assert format_answer_for_display("") == EMPTY_ANSWER_PLACEHOLDER
    assert format_answer_for_display("  ") == EMPTY_ANSWER_PLACEHOLDER
    assert format_answer_for_display("Short answer.") == "Short answer."


def test_participant_form_copy_is_self_contained() -> None:
    from eval.human_eval.form_data import (
        consent_page_text,
        form_description,
        rating_instructions_text,
        welcome_page_text,
    )

    combined = " ".join(
        [
            welcome_page_text(),
            consent_page_text(),
            rating_instructions_text(),
            form_description("P001"),
        ]
    )
    assert "eval/human_eval" not in combined
    assert "repository" not in combined.lower()
    assert "undergraduate thesis" not in combined.lower()
    assert "—" not in combined
    assert "•" not in combined
    assert "system-generated" in combined
    assert "large language model-based" in combined
    assert "Each System A, B, or C box" in combined
    assert "AI-generated" not in combined.lower()
    assert "1 to 5" in combined


def test_portal_html_embeds_form_links() -> None:
    from eval.human_eval.build_portal import build_portal_html

    html = build_portal_html({"P001": "https://example.com/form"})
    assert "P001" in html
    assert "https://example.com/form" in html
    assert "Participant code" in html

"""Tests for offline tool-routing agent."""

from __future__ import annotations

from src.baselines.offline_tool_agent import OfflineToolAgent


def test_offline_agent_parses_fatalities_and_degree_code_hyphens() -> None:
    agent = OfflineToolAgent()
    fatality = agent.answer("How many MSHA fatalities occurred in 2020?", category="trend")
    assert "29" in fatality["answer"]
    degree = agent.answer("How many degree-code-06 injuries occurred in 2014?", category="trend")
    assert "2341" in degree["answer"]

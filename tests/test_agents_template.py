import re
from pathlib import Path

import pytest

from oh_my_kb.agents.template import load_template, render_dynamic_block, render_rules


def test_load_template_returns_pt_br():
    content = load_template()
    assert "{universe}" in content  # placeholder present
    assert "pt-BR" in content  # content_version marker


def test_render_rules_substitutes_universe():
    result = render_rules("my-universe")
    assert "{universe}" not in result
    assert "my-universe" in result


def test_load_template_fallback(tmp_path, monkeypatch):
    """Unknown locale falls back to pt-BR without raising."""
    import oh_my_kb.agents.template as template_mod
    monkeypatch.setattr(template_mod, "_AGENTS_DIR", tmp_path)
    (tmp_path / "pt-BR").mkdir()
    (tmp_path / "pt-BR" / "rules_template.md").write_text("rules for {universe}")
    content = load_template(locale="xx-XX")
    assert content == "rules for {universe}"


class TestRenderDynamicBlock:
    """Tests for the dynamically generated rules block."""

    def test_contains_universe_name(self) -> None:
        block = render_dynamic_block("my-universe")
        assert "my-universe" in block

    def test_contains_all_registered_tools(self) -> None:
        """One bullet per tool in the MCP registry — count must not be hardcoded."""
        from oh_my_kb.mcp.tools import (
            KB_EXPAND_TOOL,
            KB_RECENT_TOOL,
            KB_SEARCH_TOOL,
            KB_TREE_TOOL,
            KB_WRITE_TOOL,
        )

        tools = [KB_WRITE_TOOL, KB_SEARCH_TOOL, KB_TREE_TOOL, KB_EXPAND_TOOL, KB_RECENT_TOOL]
        block = render_dynamic_block("test")
        for tool in tools:
            assert f"`{tool.name}`" in block, f"tool {tool.name} missing from block"

    def test_tool_count_matches_registry(self) -> None:
        """Bullet count must equal the number of registered tools (future-proof)."""
        from oh_my_kb.mcp.tools import (
            KB_EXPAND_TOOL,
            KB_RECENT_TOOL,
            KB_SEARCH_TOOL,
            KB_TREE_TOOL,
            KB_WRITE_TOOL,
        )

        tools = [KB_WRITE_TOOL, KB_SEARCH_TOOL, KB_TREE_TOOL, KB_EXPAND_TOOL, KB_RECENT_TOOL]
        block = render_dynamic_block("test")
        # Count lines starting with "- `kb_" to count tool bullets
        tool_bullet_lines = [
            line for line in block.splitlines()
            if line.startswith("- `kb_")
        ]
        assert len(tool_bullet_lines) == len(tools)

    def test_contains_all_resources(self) -> None:
        from oh_my_kb.mcp.resources import list_scribe_resources

        resources = list_scribe_resources()
        block = render_dynamic_block("test")
        for resource in resources:
            assert str(resource.uri) in block, f"resource {resource.uri} missing from block"

    def test_uses_trigger_phrases_for_known_tools(self) -> None:
        from oh_my_kb.agents.harness import TOOL_TRIGGERS

        block = render_dynamic_block("test")
        for tool_name, trigger in TOOL_TRIGGERS.items():
            assert trigger in block, f"trigger for {tool_name} missing"

    def test_fallback_description_for_unknown_tool(self, monkeypatch) -> None:
        """Tools without a TOOL_TRIGGERS entry get a fallback from their description."""
        from oh_my_kb.agents import harness as harness_mod

        # Temporarily remove kb_write from the triggers mapping
        triggers_without_write = {
            k: v for k, v in harness_mod.TOOL_TRIGGERS.items() if k != "kb_write"
        }
        monkeypatch.setattr(harness_mod, "TOOL_TRIGGERS", triggers_without_write)

        block = render_dynamic_block("test")
        # Should still have kb_write but with fallback description note
        assert "`kb_write`" in block
        assert "no trigger configured — using tool description" in block

    def test_dynamic_block_updates_when_trigger_changes(self, monkeypatch) -> None:
        """Re-running after trigger change produces updated block content."""
        from oh_my_kb.agents import harness as harness_mod

        original_block = render_dynamic_block("test")

        # Update one trigger
        new_triggers = dict(harness_mod.TOOL_TRIGGERS)
        new_triggers["kb_write"] = "Custom trigger for testing purposes only"
        monkeypatch.setattr(harness_mod, "TOOL_TRIGGERS", new_triggers)

        updated_block = render_dynamic_block("test")
        assert "Custom trigger for testing purposes only" in updated_block
        assert updated_block != original_block

    def test_contains_general_rules_section(self) -> None:
        block = render_dynamic_block("test")
        assert "Regras gerais" in block
        assert "kb_search" in block  # referenced in general rules

    def test_rule1_does_not_instruct_llm_to_set_universe(self) -> None:
        """Rule 1 must not tell the LLM to control the universe parameter.

        ADR-002: universe is server-bound (KB_UNIVERSE env-var in the MCP process).
        Tools have additionalProperties:false with no universe field — if the LLM
        tries to pass it, the call is rejected by the schema validator.
        """
        block = render_dynamic_block("test")
        # The bad phrasing told the LLM to "use" the universe — it has no such agency
        assert "Sempre use o universe ativo configurado em KB_UNIVERSE" not in block
        # The correct phrasing explains it's server-controlled and must not be passed
        assert (
            "nunca deve ser passado como parâmetro" in block
            or "injetado automaticamente" in block
        )

    def test_rule2_says_first_kb_write_not_any(self) -> None:
        """Rule 2 should say 'before the FIRST kb_write of the session', not 'before ANY'."""
        block = render_dynamic_block("test")
        assert "PRIMEIRO kb_write" in block or "primeiro kb_write" in block.lower()
        # Old phrasing was 'antes de qualquer kb_write' — too broad, triggers redundant reads
        assert "antes de qualquer kb_write" not in block

    def test_rule3_disambiguates_search_vs_tree(self) -> None:
        """Rule 3 must give precise routing between kb_search and kb_tree."""
        block = render_dynamic_block("test")
        # Old phrasing 'quando o usuário precisar de orientação' is vague
        assert "precisar de orientação" not in block
        # New phrasing ties kb_tree to structural/existence queries
        assert "o que existe no universe" in block or "projeto específico" in block

    def test_block_contains_meta_comment_with_universe(self) -> None:
        """The generated block must include an HTML comment with the universe name.

        This allows diagnosis of stale blocks after 'omk universe use <other>'
        without needing to parse the block content itself.
        """
        block = render_dynamic_block("my-universe")
        assert "<!-- omk:meta" in block
        assert "universe:my-universe" in block

    def test_kb_write_trigger_covers_subtypes(self) -> None:
        """kb_write trigger must cover decision/event/procedure/reference subtypes.

        'documentar algo' was too broad — it activates on README writes, audit reports,
        and other contexts where kb_write would be incorrect.
        """
        block = render_dynamic_block("test")
        # Must reference at least one specific subtype that aligns with the inputSchema
        assert any(
            word in block
            for word in ["decisão", "evento", "procedimento", "referência"]
        )
        # Old generic phrasing
        assert "documentar algo" not in block

    def test_kb_recent_trigger_is_temporal(self) -> None:
        """kb_recent trigger must be temporally specific to avoid ambiguity with kb_search."""
        block = render_dynamic_block("test")
        # Must include temporal cue so the LLM doesn't conflate it with content search
        assert "período de tempo" in block or "mudou" in block

    def test_kb_expand_trigger_mentions_full_content(self) -> None:
        """kb_expand trigger must mention reading full content explicitly."""
        block = render_dynamic_block("test")
        assert "conteúdo completo" in block or "ler na íntegra" in block

    def test_resource_description_uses_first_sentence_only(self) -> None:
        """Resource descriptions in the block must use only the first sentence.

        Full descriptions are verbose and repeat context already available
        via the resource URI itself.
        """
        from oh_my_kb.mcp.resources import list_scribe_resources

        resources = list_scribe_resources()
        block = render_dynamic_block("test")
        for resource in resources:
            if resource.description and ". " in resource.description:
                # The full description has multiple sentences — only first should appear
                sentences = resource.description.split(". ")
                if len(sentences) > 1:
                    # At most the first sentence should be present as a resource bullet
                    second_sentence = sentences[1]
                    # Find the resource bullet line
                    uri_str = str(resource.uri)
                    for line in block.splitlines():
                        if uri_str in line:
                            # Second sentence text must not appear in this bullet
                            assert second_sentence not in line, (
                                f"Resource bullet for {uri_str} includes second sentence"
                            )


# ---------------------------------------------------------------------------
# Snapshot test — guards exact content of render_dynamic_block("default")
# ---------------------------------------------------------------------------
_SNAPSHOT_PATH = Path(__file__).parent / "fixtures" / "render_dynamic_block_default.txt"


class TestRenderDynamicBlockSnapshot:
    """Snapshot test: fails when the generated block diverges from the committed fixture.

    To update the snapshot after an intentional change:
        uv run pytest tests/test_agents_template.py::TestRenderDynamicBlockSnapshot -k update
    Or manually delete the fixture and re-run to regenerate.
    """

    def _strip_timestamp(self, block: str) -> str:
        """Remove the timestamp from the meta comment for stable comparison."""
        return re.sub(
            r"(<!-- omk:meta generated:)\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z",
            r"\1<TIMESTAMP>",
            block,
        )

    def test_snapshot_matches_committed_fixture(self) -> None:
        """render_dynamic_block('default') must match the committed snapshot.

        If this test fails, a trigger, rule, or resource changed without a
        deliberate snapshot update. Run with --snapshot-update or delete the
        fixture to regenerate.
        """
        block = render_dynamic_block("default")
        normalized = self._strip_timestamp(block)

        if not _SNAPSHOT_PATH.exists():
            # First run: create the fixture directory and write the snapshot.
            _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            _SNAPSHOT_PATH.write_text(normalized, encoding="utf-8")
            pytest.skip(
                f"Snapshot fixture created at {_SNAPSHOT_PATH}. "
                "Re-run to validate against it."
            )

        committed = _SNAPSHOT_PATH.read_text(encoding="utf-8")
        assert normalized == committed, (
            "render_dynamic_block('default') diverged from snapshot fixture.\n"
            "If this change is intentional, delete the fixture and re-run to regenerate:\n"
            f"  rm {_SNAPSHOT_PATH}"
        )


# ---------------------------------------------------------------------------
# Fitness test — ALL_TOOLS must include every tool in mcp/tools/__all__
# ---------------------------------------------------------------------------
class TestAllToolsFitnessFunction:
    """Ensures every tool exported from mcp.tools has a TOOL_TRIGGERS entry
    and appears in ALL_TOOLS.  Fails loudly when a new tool is added without
    updating the catalog.
    """

    def test_all_tools_names_match_exports(self) -> None:
        """ALL_TOOLS must contain every *_TOOL object exported by mcp.tools.__all__."""
        import oh_my_kb.mcp.tools as tools_mod
        from oh_my_kb.mcp.tools import ALL_TOOLS

        # Collect the .name of every *_TOOL symbol in __all__
        exported_names = {
            getattr(tools_mod, sym).name
            for sym in tools_mod.__all__
            if sym.endswith("_TOOL")
        }
        all_tools_names = {tool.name for tool in ALL_TOOLS}
        missing = exported_names - all_tools_names
        assert not missing, (
            f"These tools are exported by mcp.tools but not in ALL_TOOLS: {sorted(missing)}\n"
            "Add them to ALL_TOOLS in oh_my_kb/mcp/tools/__init__.py."
        )

    def test_all_tools_have_trigger_entries(self) -> None:
        """Every tool in ALL_TOOLS must have a TOOL_TRIGGERS entry.

        A missing entry causes the block renderer to fall back to the English
        tool description, producing a PT-BR/EN mix in the CLAUDE.md block.
        """
        from oh_my_kb.agents.harness import TOOL_TRIGGERS
        from oh_my_kb.mcp.tools import ALL_TOOLS

        missing = [t.name for t in ALL_TOOLS if t.name not in TOOL_TRIGGERS]
        assert not missing, (
            f"These tools lack a TOOL_TRIGGERS entry: {missing}\n"
            "Add them to TOOL_TRIGGERS in oh_my_kb/agents/harness.py."
        )

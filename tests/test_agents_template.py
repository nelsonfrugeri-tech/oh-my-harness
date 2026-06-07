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

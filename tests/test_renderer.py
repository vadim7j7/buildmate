"""Tests for renderer module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import compose_stacks
from lib.renderer import RenderedOutput, render_all


class TestRenderAll:
    """Tests for render_all function."""

    def test_render_rails_stack(self):
        """Should render rails stack without errors."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert isinstance(output, RenderedOutput)
        assert len(output.agents) > 0
        assert "orchestrator.md" in output.agents
        assert "grind.md" in output.agents
        assert "backend-developer.md" in output.agents

    def test_render_nextjs_stack(self):
        """Should render nextjs stack without errors."""
        composed = compose_stacks(["nextjs"])
        output = render_all(composed)

        assert "frontend-developer.md" in output.agents
        assert "frontend-tester.md" in output.agents

    def test_render_react_native_stack(self):
        """Should render react-native stack without errors."""
        composed = compose_stacks(["react-native"])
        output = render_all(composed)

        assert "mobile-developer.md" in output.agents

    def test_render_fastapi_stack(self):
        """Should render fastapi stack without errors."""
        composed = compose_stacks(["fastapi"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents

    def test_render_multi_stack(self):
        """Should render multi-stack composition."""
        composed = compose_stacks(["rails", "nextjs"])
        output = render_all(composed)

        # Should have agents from both
        assert "backend-developer.md" in output.agents
        assert "frontend-developer.md" in output.agents

        # Orchestrator should mention both stacks
        orchestrator_content = output.agents["orchestrator.md"]
        assert (
            "rails" in orchestrator_content.lower() or "Rails" in orchestrator_content
        )

    def test_render_includes_base_agents(self):
        """Should include base agents (orchestrator, grind, eval, security)."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert "orchestrator.md" in output.agents
        assert "grind.md" in output.agents
        assert "eval-agent.md" in output.agents
        assert "security-auditor.md" in output.agents

    def test_render_claude_md(self):
        """Should render CLAUDE.md template."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert output.claude_md is not None
        assert len(output.claude_md) > 0
        assert "rails" in output.claude_md.lower() or "Rails" in output.claude_md

    def test_render_readme(self):
        """Should render README.md template."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert output.readme is not None
        assert len(output.readme) > 0

    def test_agent_content_has_frontmatter(self):
        """Rendered agents should have YAML frontmatter."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        # Check backend-developer has frontmatter
        content = output.agents["backend-developer.md"]
        assert content.startswith("---")
        assert "name:" in content
        assert "tools:" in content

    def test_quality_gates_in_agents(self):
        """Rendered agents should include quality gates."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        # Developer agent should mention quality gate commands
        content = output.agents["backend-developer.md"]
        assert "rubocop" in content.lower() or "rspec" in content.lower()

    def test_patterns_collected(self):
        """Patterns should be collected from stacks."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert len(output.patterns) > 0

    def test_styles_collected(self):
        """Styles should be collected from stacks."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert len(output.styles) > 0

    def test_skills_collected(self):
        """Skills should be collected from base and stacks."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert len(output.skills) > 0


class TestRenderedOutput:
    """Tests for RenderedOutput dataclass."""

    def test_rendered_output_properties(self):
        """RenderedOutput should have expected properties."""
        output = RenderedOutput(
            agents={"test.md": "content"},
            claude_md="# Project",
            readme="# README",
            settings={"key": "value"},
        )

        assert output.agents == {"test.md": "content"}
        assert output.claude_md == "# Project"
        assert output.readme == "# README"
        assert output.settings == {"key": "value"}

    def test_rendered_output_defaults(self):
        """RenderedOutput should have sensible defaults."""
        output = RenderedOutput()

        assert output.agents == {}
        assert output.claude_md == ""
        assert output.readme == ""
        assert output.settings == {}
        assert output.patterns == {}
        assert output.styles == {}
        assert output.skills == {}

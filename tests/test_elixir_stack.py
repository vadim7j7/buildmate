"""Tests for the elixir and phoenix stacks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import (
    compose_stacks,
    load_stack,
)
from lib.renderer import render_all


class TestLoadElixirStack:
    """Tests for loading the elixir parent stack."""

    def test_load_elixir_stack(self):
        """Should load elixir stack with expected agents, gates, and patterns."""
        config = load_stack("elixir")

        assert config.name == "elixir"
        assert config.display_name == "Elixir"
        assert config.extends is None

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names
        assert len(config.agents) == 3

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "dialyzer" in config.quality_gates
        assert "tests" in config.quality_gates

        assert "patterns/backend-patterns.md" in config.patterns
        assert "styles/backend-elixir.md" in config.styles

    def test_elixir_stack_variables(self):
        """Elixir stack should have expected variables."""
        config = load_stack("elixir")

        assert config.variables["framework"] == "Elixir"
        assert config.variables["language"] == "Elixir 1.16+"
        assert config.variables["runtime"] == "BEAM/OTP 26+"
        assert config.variables["test_framework"] == "ExUnit"
        assert config.variables["orm"] == "Ecto"
        assert config.variables["linter"] == "Credo"

    def test_elixir_stack_options(self):
        """Elixir stack should have db option."""
        config = load_stack("elixir")

        assert "db" in config.options
        db_option = config.options["db"]
        assert db_option.default == "postgresql"
        assert "postgresql" in db_option.choices
        assert "mysql" in db_option.choices
        assert "sqlite" in db_option.choices

    def test_elixir_stack_skills(self):
        """Elixir stack should have expected skills."""
        config = load_stack("elixir")

        expected_skills = ["test", "review", "docs", "verify", "new-module", "new-genserver", "new-supervisor"]
        for skill in expected_skills:
            assert skill in config.skills

    def test_validate_elixir_stack(self):
        """Elixir stack should pass validation."""
        config = load_stack("elixir", validate=True)
        assert config.name == "elixir"


class TestLoadPhoenix:
    """Tests for loading the phoenix stack with extends: elixir."""

    def test_load_phoenix_stack(self):
        """Should load phoenix stack with extends resolved."""
        config = load_stack("phoenix")

        assert config.name == "phoenix"
        assert config.display_name == "Phoenix Framework"
        assert config.parent_stack_path is not None

    def test_phoenix_inherits_quality_gates(self):
        """Phoenix should inherit quality gates from elixir."""
        config = load_stack("phoenix")

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "dialyzer" in config.quality_gates
        assert "tests" in config.quality_gates
        assert config.quality_gates["format"].command == "mix format --check-formatted"

    def test_phoenix_inherits_styles(self):
        """Phoenix should inherit styles from elixir parent."""
        config = load_stack("phoenix")

        assert "styles/backend-elixir.md" in config.styles

    def test_phoenix_overrides_developer_agent(self):
        """Phoenix should override backend-developer but inherit tester and reviewer."""
        config = load_stack("phoenix")

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

        dev = next(a for a in config.agents if a.name == "backend-developer")
        assert dev.source_stack == "phoenix"

        tester = next(a for a in config.agents if a.name == "backend-tester")
        assert tester.source_stack == "elixir"

        reviewer = next(a for a in config.agents if a.name == "backend-reviewer")
        assert reviewer.source_stack == "elixir"

    def test_phoenix_has_own_skills(self):
        """Phoenix should have its own skills plus inherited ones."""
        config = load_stack("phoenix")

        # Phoenix-specific
        assert "new-context" in config.skills
        assert "new-live" in config.skills
        assert "new-controller" in config.skills
        assert "new-channel" in config.skills
        # Inherited from elixir
        assert "test" in config.skills
        assert "review" in config.skills
        assert "new-module" in config.skills
        assert "new-genserver" in config.skills

    def test_phoenix_patterns_merged(self):
        """Both elixir and phoenix patterns should be present."""
        config = load_stack("phoenix")

        # Elixir parent pattern
        assert "patterns/backend-patterns.md" in config.patterns
        # Phoenix-specific pattern
        assert "patterns/phoenix-patterns.md" in config.patterns

    def test_phoenix_variables_override(self):
        """Phoenix should override framework but inherit language from elixir."""
        config = load_stack("phoenix")

        assert config.variables["framework"] == "Phoenix 1.7+"
        assert config.variables["language"] == "Elixir 1.16+"
        assert config.variables["runtime"] == "BEAM/OTP 26+"
        assert config.variables["orm"] == "Ecto"
        assert config.variables["template_engine"] == "HEEx"
        assert config.variables["realtime"] == "Phoenix.PubSub"

    def test_phoenix_has_verification(self):
        """Phoenix stack.yaml should have verification section."""
        import yaml

        stack_yaml = Path(__file__).parent.parent / "stacks" / "phoenix" / "stack.yaml"
        with open(stack_yaml) as f:
            raw = yaml.safe_load(f)

        assert "verification" in raw
        assert raw["verification"]["enabled"] is True
        assert raw["verification"]["dev_server"]["port"] == 4000

    def test_validate_phoenix_stack(self):
        """Phoenix stack should pass validation."""
        config = load_stack("phoenix", validate=True)
        assert config.name == "phoenix"


class TestComposePhoenix:
    """Tests for composing phoenix with other stacks."""

    def test_compose_phoenix_single(self):
        """compose_stacks(['phoenix']) should work."""
        composed = compose_stacks(["phoenix"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "phoenix"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

    def test_compose_phoenix_with_nextjs(self):
        """Phoenix + nextjs multi-stack composition should work."""
        composed = compose_stacks(["phoenix", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names

        assert "phoenix" in composed.all_quality_gates
        assert "nextjs" in composed.all_quality_gates


class TestRenderPhoenix:
    """Tests for rendering phoenix stack templates."""

    def test_render_phoenix_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["phoenix"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_phoenix_developer_content(self):
        """Phoenix developer agent should contain Phoenix-specific content."""
        composed = compose_stacks(["phoenix"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Phoenix" in dev_content


class TestRenderElixir:
    """Tests for rendering elixir stack templates standalone."""

    def test_render_elixir_stack(self):
        """Full render of standalone elixir should produce expected agents."""
        composed = compose_stacks(["elixir"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_elixir_developer_content(self):
        """Elixir developer agent should contain Elixir-specific content."""
        composed = compose_stacks(["elixir"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Elixir" in dev_content

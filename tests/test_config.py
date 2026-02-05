"""Tests for config loading module."""

import pytest
from pathlib import Path
import tempfile
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import (
    load_stack,
    compose_stacks,
    parse_stack_arg,
    StackConfig,
    Agent,
    QualityGate,
    ComposedConfig,
)


class TestParseStackArg:
    """Tests for parse_stack_arg function."""

    def test_single_stack(self):
        """Single stack name should return list with one item."""
        result = parse_stack_arg("rails")
        assert result == ["rails"]

    def test_multiple_stacks(self):
        """Comma-separated stacks should return list."""
        result = parse_stack_arg("rails,nextjs")
        assert result == ["rails", "nextjs"]

    def test_multiple_stacks_with_spaces(self):
        """Stacks with spaces should be trimmed."""
        result = parse_stack_arg("rails, nextjs, fastapi")
        assert result == ["rails", "nextjs", "fastapi"]

    def test_empty_string(self):
        """Empty string should return empty list."""
        result = parse_stack_arg("")
        assert result == []


class TestLoadStack:
    """Tests for load_stack function."""

    def test_load_rails_stack(self):
        """Should load rails stack config."""
        config = load_stack("rails")

        assert config.name == "rails"
        assert config.display_name == "Ruby on Rails API"
        assert len(config.agents) > 0
        assert len(config.skills) > 0
        assert len(config.quality_gates) > 0

    def test_load_nextjs_stack(self):
        """Should load nextjs stack config."""
        config = load_stack("nextjs")

        assert config.name == "nextjs"
        assert "frontend-developer" in [a.name for a in config.agents]

    def test_load_react_native_stack(self):
        """Should load react-native stack config."""
        config = load_stack("react-native")

        assert config.name == "react-native"
        assert "mobile-developer" in [a.name for a in config.agents]

    def test_load_fastapi_stack(self):
        """Should load fastapi stack config."""
        config = load_stack("fastapi")

        assert config.name == "fastapi"
        assert "backend-developer" in [a.name for a in config.agents]

    def test_load_nonexistent_stack(self):
        """Should raise error for nonexistent stack."""
        with pytest.raises(FileNotFoundError):
            load_stack("nonexistent")


class TestStackConfig:
    """Tests for StackConfig dataclass."""

    def test_agent_properties(self):
        """Agent should have expected properties."""
        agent = Agent(
            name="test-agent",
            template="agents/test.md.j2",
            description="Test description",
            tools=["Read", "Write"],
            model="opus",
        )
        assert agent.name == "test-agent"
        assert agent.template == "agents/test.md.j2"
        assert agent.tools == ["Read", "Write"]
        assert agent.model == "opus"

    def test_quality_gate_properties(self):
        """QualityGate should have expected properties."""
        gate = QualityGate(
            name="lint",
            command="npm run lint",
            fix_command="npm run lint --fix",
            description="Linting",
        )
        assert gate.name == "lint"
        assert gate.command == "npm run lint"
        assert gate.fix_command == "npm run lint --fix"
        assert gate.description == "Linting"

    def test_stack_config_from_load(self):
        """StackConfig from load_stack should have expected properties."""
        config = load_stack("rails")

        assert config.name == "rails"
        assert config.display_name == "Ruby on Rails API"
        assert isinstance(config.agents, list)
        assert isinstance(config.quality_gates, dict)
        assert config.stack_path.exists()


class TestComposeStacks:
    """Tests for compose_stacks function."""

    def test_compose_single_stack(self):
        """Composing single stack should work."""
        composed = compose_stacks(["rails"])

        assert isinstance(composed, ComposedConfig)
        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "rails"
        assert len(composed.all_agents) > 0

    def test_compose_multiple_stacks(self):
        """Composing multiple stacks should merge them."""
        composed = compose_stacks(["rails", "nextjs"])

        assert len(composed.stacks) == 2

        # Should have agents from both stacks
        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names

    def test_compose_merges_quality_gates(self):
        """Composing stacks should merge quality gates."""
        composed = compose_stacks(["rails", "nextjs"])

        # Should have quality gates from both
        assert "rails" in composed.all_quality_gates
        assert "nextjs" in composed.all_quality_gates

    def test_compose_merges_skills(self):
        """Composing stacks should merge skills."""
        composed = compose_stacks(["rails", "nextjs"])

        # Should have skills from both (deduplicated)
        assert "test" in composed.all_skills
        assert "review" in composed.all_skills

    def test_compose_merges_patterns_and_styles(self):
        """Composing stacks should merge patterns and styles."""
        composed = compose_stacks(["rails", "nextjs"])

        # Should have patterns/styles from both
        assert len(composed.all_patterns) >= 2
        assert len(composed.all_styles) >= 2

    def test_composed_config_has_stacks_property(self):
        """ComposedConfig should have stacks list."""
        composed = compose_stacks(["rails"])

        assert hasattr(composed, "stacks")
        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "rails"

    def test_composed_config_has_default_model(self):
        """ComposedConfig should have default_model."""
        composed = compose_stacks(["rails"])

        assert hasattr(composed, "default_model")
        assert composed.default_model in ["opus", "sonnet", "haiku"]

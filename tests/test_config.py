"""Tests for config loading module."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import (
    Agent,
    ComposedConfig,
    QualityGate,
    _resolve_inheritance,
    compose_stacks,
    load_stack,
    parse_stack_arg,
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


class TestStackInheritance:
    """Tests for stack inheritance via extends."""

    def _make_parent(self, tmp_path):
        """Create a minimal parent stack config dict and directory."""
        parent_dir = tmp_path / "parent-stack"
        parent_dir.mkdir()
        return {
            "name": "parent-stack",
            "display_name": "Parent Stack",
            "description": "A parent stack",
            "default_model": "sonnet",
            "compatible_with": ["nextjs"],
            "agents": [
                {"name": "dev-agent", "template": "agents/dev.md.j2", "tools": ["Read", "Write"]},
                {"name": "test-agent", "template": "agents/test.md.j2", "tools": ["Bash"]},
            ],
            "skills": ["test", "review"],
            "quality_gates": {
                "lint": {"command": "lint-cmd"},
                "test": {"command": "test-cmd"},
            },
            "patterns": ["patterns/p1.md"],
            "styles": ["styles/s1.md"],
            "variables": {"language": "Ruby", "framework": "Rails"},
            "options": {
                "ui": {
                    "description": "UI library",
                    "default": "tailwind",
                    "choices": {
                        "tailwind": {"description": "Tailwind CSS"},
                    },
                }
            },
        }, parent_dir

    def _write_parent_yaml(self, parent_config, parent_dir):
        """Write a parent stack.yaml to disk (for real resolution via STACKS_DIR)."""
        import yaml

        stack_yaml = parent_dir / "stack.yaml"
        with open(stack_yaml, "w") as f:
            yaml.dump(parent_config, f)

    def _make_child(self, parent_name="parent-stack"):
        """Create a minimal child config dict."""
        return {
            "name": "child-stack",
            "extends": parent_name,
        }

    def test_no_extends_passthrough(self):
        """Config without extends should be returned unchanged."""
        config = {"name": "plain", "display_name": "Plain", "agents": [], "skills": [], "quality_gates": {}}
        resolved, parent_path = _resolve_inheritance(config, Path("/fake"))
        assert resolved is config
        assert parent_path is None

    def test_agents_inherited(self, tmp_path, monkeypatch):
        """Parent agents should appear in resolved output."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        resolved, parent_path = _resolve_inheritance(child, tmp_path / "child-stack")

        agent_names = [a["name"] for a in resolved["agents"]]
        assert "dev-agent" in agent_names
        assert "test-agent" in agent_names
        assert parent_path == parent_dir

    def test_child_agent_overrides_parent(self, tmp_path, monkeypatch):
        """Child agent with same name should replace parent's."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        child["agents"] = [
            {"name": "dev-agent", "template": "agents/custom-dev.md.j2", "tools": ["Read", "Write", "Bash"]},
        ]
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        agents_by_name = {a["name"]: a for a in resolved["agents"]}
        assert agents_by_name["dev-agent"]["template"] == "agents/custom-dev.md.j2"
        assert agents_by_name["dev-agent"]["tools"] == ["Read", "Write", "Bash"]
        # Parent's test-agent should still be present
        assert "test-agent" in agents_by_name

    def test_source_stack_set_correctly(self, tmp_path, monkeypatch):
        """Inherited agents tagged with parent name, child agents with child name."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        child["agents"] = [
            {"name": "new-agent", "template": "agents/new.md.j2", "tools": ["Read"]},
        ]
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        agents_by_name = {a["name"]: a for a in resolved["agents"]}
        # Inherited agents should have parent's _source_stack
        assert agents_by_name["dev-agent"]["_source_stack"] == "parent-stack"
        assert agents_by_name["test-agent"]["_source_stack"] == "parent-stack"
        # Child's own agent should have child's _source_stack
        assert agents_by_name["new-agent"]["_source_stack"] == "child-stack"

    def test_skills_merged(self, tmp_path, monkeypatch):
        """Skills should be union of parent + child, deduplicated."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        child["skills"] = ["review", "deploy"]  # "review" duplicates parent
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        assert resolved["skills"] == ["test", "review", "deploy"]

    def test_quality_gates_child_overrides(self, tmp_path, monkeypatch):
        """Child quality gate should override parent gate with same name."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        child["quality_gates"] = {
            "lint": {"command": "child-lint-cmd"},
        }
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        assert resolved["quality_gates"]["lint"]["command"] == "child-lint-cmd"
        # Parent's test gate should still be present
        assert resolved["quality_gates"]["test"]["command"] == "test-cmd"

    def test_variables_child_overrides(self, tmp_path, monkeypatch):
        """Child variables should override parent variables."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        child["variables"] = {"language": "Python", "new_var": "value"}
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        assert resolved["variables"]["language"] == "Python"
        assert resolved["variables"]["framework"] == "Rails"  # from parent
        assert resolved["variables"]["new_var"] == "value"

    def test_patterns_merged(self, tmp_path, monkeypatch):
        """Both parent and child patterns should be present."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        child["patterns"] = ["patterns/p2.md"]
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        assert "patterns/p1.md" in resolved["patterns"]
        assert "patterns/p2.md" in resolved["patterns"]

    def test_compatible_with_union(self, tmp_path, monkeypatch):
        """compatible_with should be union of both parent and child."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        child["compatible_with"] = ["fastapi"]
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        assert "nextjs" in resolved["compatible_with"]
        assert "fastapi" in resolved["compatible_with"]

    def test_display_name_inherited(self, tmp_path, monkeypatch):
        """Child should inherit display_name from parent if omitted."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        assert resolved["display_name"] == "Parent Stack"

    def test_options_inherited(self, tmp_path, monkeypatch):
        """Parent options should be available in child."""
        parent_config, parent_dir = self._make_parent(tmp_path)
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        resolved, _ = _resolve_inheritance(child, tmp_path / "child-stack")

        assert "ui" in resolved["options"]
        assert resolved["options"]["ui"]["default"] == "tailwind"

    def test_multi_level_raises(self, tmp_path, monkeypatch):
        """Parent with extends should raise ValueError."""
        # Create grandparent
        grandparent_dir = tmp_path / "grandparent"
        grandparent_dir.mkdir()

        # Create parent that also extends
        parent_config = {
            "name": "parent-stack",
            "extends": "grandparent",
            "display_name": "Parent",
            "agents": [],
            "skills": [],
            "quality_gates": {},
        }
        parent_dir = tmp_path / "parent-stack"
        parent_dir.mkdir()
        self._write_parent_yaml(parent_config, parent_dir)
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = self._make_child()
        with pytest.raises(ValueError, match="Multi-level inheritance"):
            _resolve_inheritance(child, tmp_path / "child-stack")

    def test_self_extends_raises(self):
        """Extending self should raise ValueError."""
        config = {"name": "my-stack", "extends": "my-stack"}
        with pytest.raises(ValueError, match="cannot extend itself"):
            _resolve_inheritance(config, Path("/fake"))

    def test_nonexistent_parent_raises(self, tmp_path, monkeypatch):
        """Missing parent should raise FileNotFoundError."""
        monkeypatch.setattr("lib.config.STACKS_DIR", tmp_path)

        child = {"name": "child-stack", "extends": "nonexistent-parent"}
        with pytest.raises(FileNotFoundError, match="nonexistent-parent"):
            _resolve_inheritance(child, tmp_path / "child-stack")

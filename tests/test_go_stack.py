"""Tests for the go, gin, fiber, and chi stacks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import (
    compose_stacks,
    load_stack,
)
from lib.renderer import render_all


class TestLoadGoStack:
    """Tests for loading the go parent stack."""

    def test_load_go_stack(self):
        """Should load go stack with expected agents, gates, and patterns."""
        config = load_stack("go")

        assert config.name == "go"
        assert config.display_name == "Go"
        assert config.extends is None

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names
        assert len(config.agents) == 3

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates

        assert "patterns/backend-patterns.md" in config.patterns
        assert "styles/backend-go.md" in config.styles

    def test_go_stack_variables(self):
        """Go stack should have expected variables."""
        config = load_stack("go")

        assert config.variables["framework"] == "Go"
        assert config.variables["language"] == "Go 1.22+"
        assert config.variables["test_framework"] == "testing + testify"
        assert config.variables["orm"] == "database/sql"

    def test_go_stack_options(self):
        """Go stack should have db option."""
        config = load_stack("go")

        assert "db" in config.options
        db_option = config.options["db"]
        assert db_option.default == "postgresql"
        assert "postgresql" in db_option.choices
        assert "mysql" in db_option.choices
        assert "sqlite" in db_option.choices
        assert "mongodb" in db_option.choices

    def test_go_stack_skills(self):
        """Go stack should have expected skills."""
        config = load_stack("go")

        expected_skills = ["test", "review", "docs", "verify", "new-handler", "new-service", "new-model"]
        for skill in expected_skills:
            assert skill in config.skills

    def test_validate_go_stack(self):
        """Go stack should pass validation."""
        config = load_stack("go", validate=True)
        assert config.name == "go"


class TestLoadGin:
    """Tests for loading the gin stack with extends: go."""

    def test_load_gin_stack(self):
        """Should load gin stack with extends resolved."""
        config = load_stack("gin")

        assert config.name == "gin"
        assert config.display_name == "Gin Web Framework"
        assert config.parent_stack_path is not None

    def test_gin_inherits_quality_gates(self):
        """Gin should inherit quality gates from go."""
        config = load_stack("gin")

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates
        assert config.quality_gates["format"].command == "gofmt -l ."

    def test_gin_inherits_styles(self):
        """Gin should inherit styles from go parent."""
        config = load_stack("gin")

        assert "styles/backend-go.md" in config.styles

    def test_gin_overrides_developer_agent(self):
        """Gin should override backend-developer but inherit tester and reviewer."""
        config = load_stack("gin")

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

        dev = next(a for a in config.agents if a.name == "backend-developer")
        assert dev.source_stack == "gin"

        tester = next(a for a in config.agents if a.name == "backend-tester")
        assert tester.source_stack == "go"

        reviewer = next(a for a in config.agents if a.name == "backend-reviewer")
        assert reviewer.source_stack == "go"

    def test_gin_has_own_skills(self):
        """Gin should have its own skills plus inherited ones."""
        config = load_stack("gin")

        # Gin-specific
        assert "new-router" in config.skills
        assert "new-middleware" in config.skills
        assert "new-handler" in config.skills
        # Inherited from go
        assert "test" in config.skills
        assert "review" in config.skills

    def test_gin_has_verification(self):
        """Gin stack.yaml should have verification section."""
        import yaml

        stack_yaml = Path(__file__).parent.parent / "stacks" / "gin" / "stack.yaml"
        with open(stack_yaml) as f:
            raw = yaml.safe_load(f)

        assert "verification" in raw
        assert raw["verification"]["enabled"] is True
        assert raw["verification"]["dev_server"]["port"] == 8080

    def test_gin_variables(self):
        """Gin should override framework but inherit language from go."""
        config = load_stack("gin")

        assert config.variables["framework"] == "Gin"
        assert config.variables["language"] == "Go 1.22+"
        assert config.variables["test_framework"] == "testing + testify"
        assert config.variables["validation"] == "go-playground/validator"

    def test_validate_gin_stack(self):
        """Gin stack should pass validation."""
        config = load_stack("gin", validate=True)
        assert config.name == "gin"


class TestLoadFiber:
    """Tests for loading the fiber stack with extends: go."""

    def test_load_fiber_stack(self):
        """Should load fiber stack with extends resolved."""
        config = load_stack("fiber")

        assert config.name == "fiber"
        assert config.display_name == "Fiber Web Framework"
        assert config.parent_stack_path is not None

    def test_fiber_inherits_from_go(self):
        """Fiber should inherit quality gates and styles from go."""
        config = load_stack("fiber")

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates
        assert "styles/backend-go.md" in config.styles

    def test_fiber_overrides_developer_agent(self):
        """Fiber should override backend-developer but inherit tester and reviewer."""
        config = load_stack("fiber")

        dev = next(a for a in config.agents if a.name == "backend-developer")
        assert dev.source_stack == "fiber"

        tester = next(a for a in config.agents if a.name == "backend-tester")
        assert tester.source_stack == "go"

    def test_fiber_has_own_skills(self):
        """Fiber should have new-router, new-middleware, new-handler skills."""
        config = load_stack("fiber")

        assert "new-router" in config.skills
        assert "new-middleware" in config.skills
        assert "new-handler" in config.skills
        assert "test" in config.skills

    def test_fiber_variables(self):
        """Fiber should override framework but inherit language from go."""
        config = load_stack("fiber")

        assert config.variables["framework"] == "Fiber v2+"
        assert config.variables["language"] == "Go 1.22+"
        assert config.variables["validation"] == "go-playground/validator"

    def test_fiber_has_verification(self):
        """Fiber stack.yaml should have verification section."""
        import yaml

        stack_yaml = Path(__file__).parent.parent / "stacks" / "fiber" / "stack.yaml"
        with open(stack_yaml) as f:
            raw = yaml.safe_load(f)

        assert "verification" in raw
        assert raw["verification"]["dev_server"]["port"] == 3000

    def test_validate_fiber_stack(self):
        """Fiber stack should pass validation."""
        config = load_stack("fiber", validate=True)
        assert config.name == "fiber"


class TestLoadChi:
    """Tests for loading the chi stack with extends: go."""

    def test_load_chi_stack(self):
        """Should load chi stack with extends resolved."""
        config = load_stack("chi")

        assert config.name == "chi"
        assert config.display_name == "Chi Router"
        assert config.parent_stack_path is not None

    def test_chi_inherits_from_go(self):
        """Chi should inherit quality gates and styles from go."""
        config = load_stack("chi")

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates
        assert "styles/backend-go.md" in config.styles

    def test_chi_overrides_developer_agent(self):
        """Chi should override backend-developer but inherit tester and reviewer."""
        config = load_stack("chi")

        dev = next(a for a in config.agents if a.name == "backend-developer")
        assert dev.source_stack == "chi"

        tester = next(a for a in config.agents if a.name == "backend-tester")
        assert tester.source_stack == "go"

    def test_chi_has_own_skills(self):
        """Chi should have new-router, new-middleware, new-handler skills."""
        config = load_stack("chi")

        assert "new-router" in config.skills
        assert "new-middleware" in config.skills
        assert "new-handler" in config.skills
        assert "test" in config.skills

    def test_chi_variables(self):
        """Chi should override framework but inherit language from go."""
        config = load_stack("chi")

        assert config.variables["framework"] == "Chi v5+"
        assert config.variables["language"] == "Go 1.22+"

    def test_validate_chi_stack(self):
        """Chi stack should pass validation."""
        config = load_stack("chi", validate=True)
        assert config.name == "chi"


class TestComposeGin:
    """Tests for composing gin with other stacks."""

    def test_compose_gin_single(self):
        """compose_stacks(['gin']) should work."""
        composed = compose_stacks(["gin"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "gin"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

    def test_compose_gin_with_nextjs(self):
        """Gin + nextjs multi-stack composition should work."""
        composed = compose_stacks(["gin", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names

        assert "gin" in composed.all_quality_gates
        assert "nextjs" in composed.all_quality_gates


class TestComposeFiber:
    """Tests for composing fiber with other stacks."""

    def test_compose_fiber_single(self):
        """compose_stacks(['fiber']) should work."""
        composed = compose_stacks(["fiber"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "fiber"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names

    def test_compose_fiber_with_nextjs(self):
        """Fiber + nextjs multi-stack composition should work."""
        composed = compose_stacks(["fiber", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names


class TestComposeChi:
    """Tests for composing chi with other stacks."""

    def test_compose_chi_single(self):
        """compose_stacks(['chi']) should work."""
        composed = compose_stacks(["chi"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "chi"

    def test_compose_chi_with_nuxt(self):
        """Chi + nuxt multi-stack composition should work."""
        composed = compose_stacks(["chi", "nuxt"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names


class TestRenderGin:
    """Tests for rendering gin stack templates."""

    def test_render_gin_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["gin"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_gin_developer_content(self):
        """Gin developer agent should contain Gin-specific content."""
        composed = compose_stacks(["gin"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Gin" in dev_content


class TestRenderFiber:
    """Tests for rendering fiber stack templates."""

    def test_render_fiber_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["fiber"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_fiber_developer_content(self):
        """Fiber developer agent should contain Fiber-specific content."""
        composed = compose_stacks(["fiber"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Fiber" in dev_content


class TestRenderChi:
    """Tests for rendering chi stack templates."""

    def test_render_chi_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["chi"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_chi_developer_content(self):
        """Chi developer agent should contain Chi-specific content."""
        composed = compose_stacks(["chi"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Chi" in dev_content

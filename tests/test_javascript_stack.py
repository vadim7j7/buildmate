"""Tests for the javascript, nextjs, express, and nuxt stacks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import (
    compose_stacks,
    load_stack,
)
from lib.renderer import render_all


class TestLoadJavaScriptStack:
    """Tests for loading the javascript parent stack."""

    def test_load_javascript_stack(self):
        """Should load javascript stack with expected properties."""
        config = load_stack("javascript")

        assert config.name == "javascript"
        assert config.display_name == "JavaScript / TypeScript"
        assert config.extends is None

    def test_javascript_variables(self):
        """JavaScript stack should have expected variables."""
        config = load_stack("javascript")

        assert config.variables["language"] == "TypeScript"
        assert config.variables["package_manager"] == "npm"
        assert config.variables["runtime"] == "Node.js 22+"

    def test_javascript_empty_agents(self):
        """JavaScript stack should have empty agents list."""
        config = load_stack("javascript")

        assert len(config.agents) == 0

    def test_javascript_quality_gates(self):
        """JavaScript stack should have quality gates."""
        config = load_stack("javascript")

        assert "typecheck" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates

    def test_validate_javascript_stack(self):
        """JavaScript stack should pass validation."""
        config = load_stack("javascript", validate=True)
        assert config.name == "javascript"


class TestLoadNextjsRefactored:
    """Tests for loading the refactored nextjs stack with extends: javascript."""

    def test_load_nextjs_stack(self):
        """Should load nextjs stack with extends resolved."""
        config = load_stack("nextjs")

        assert config.name == "nextjs"
        assert config.display_name == "React + Next.js"
        assert config.parent_stack_path is not None

    def test_nextjs_inherits_quality_gates(self):
        """Next.js should inherit quality gates from javascript."""
        config = load_stack("nextjs")

        assert "typecheck" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates

    def test_nextjs_has_own_agents(self):
        """Next.js should have frontend-* agents (parent has none)."""
        config = load_stack("nextjs")

        agent_names = [a.name for a in config.agents]
        assert "frontend-developer" in agent_names
        assert "frontend-tester" in agent_names
        assert "frontend-reviewer" in agent_names
        assert len(config.agents) == 3

    def test_nextjs_patterns_merged(self):
        """Both javascript and nextjs patterns should be present."""
        config = load_stack("nextjs")

        # JavaScript parent pattern
        assert "patterns/typescript-patterns.md" in config.patterns
        # Next.js-specific patterns
        assert "patterns/frontend-patterns.md" in config.patterns

    def test_nextjs_styles_merged(self):
        """Both javascript and nextjs styles should be present."""
        config = load_stack("nextjs")

        # JavaScript parent style
        assert "styles/typescript.md" in config.styles
        # Next.js-specific style
        assert "styles/frontend-typescript.md" in config.styles

    def test_validate_nextjs_stack(self):
        """Next.js stack should pass validation."""
        config = load_stack("nextjs", validate=True)
        assert config.name == "nextjs"


class TestLoadExpress:
    """Tests for loading the express stack with extends: javascript."""

    def test_load_express_stack(self):
        """Should load express stack with extends resolved."""
        config = load_stack("express")

        assert config.name == "express"
        assert config.display_name == "Express.js API"
        assert config.parent_stack_path is not None

    def test_express_inherits_from_javascript(self):
        """Express should inherit quality gates from javascript."""
        config = load_stack("express")

        assert "typecheck" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates

    def test_express_has_backend_agents(self):
        """Express should have backend-* agents."""
        config = load_stack("express")

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names
        assert len(config.agents) == 3

    def test_express_has_own_skills(self):
        """Express should have router, middleware, controller skills."""
        config = load_stack("express")

        assert "new-router" in config.skills
        assert "new-middleware" in config.skills
        assert "new-controller" in config.skills
        # Inherited
        assert "test" in config.skills
        assert "review" in config.skills

    def test_express_has_verification(self):
        """Express stack.yaml should have verification section."""
        import yaml

        stack_yaml = Path(__file__).parent.parent / "stacks" / "express" / "stack.yaml"
        with open(stack_yaml) as f:
            raw = yaml.safe_load(f)

        assert "verification" in raw
        assert raw["verification"]["dev_server"]["port"] == 3000

    def test_express_variables(self):
        """Express should have framework-specific variables."""
        config = load_stack("express")

        assert config.variables["framework"] == "Express 5+"
        assert config.variables["language"] == "TypeScript"  # inherited
        assert config.variables["orm"] == "Prisma"
        assert config.variables["validation"] == "Zod"

    def test_validate_express_stack(self):
        """Express stack should pass validation."""
        config = load_stack("express", validate=True)
        assert config.name == "express"


class TestLoadNuxt:
    """Tests for loading the nuxt stack with extends: javascript."""

    def test_load_nuxt_stack(self):
        """Should load nuxt stack with extends resolved."""
        config = load_stack("nuxt")

        assert config.name == "nuxt"
        assert config.display_name == "Nuxt 3"
        assert config.parent_stack_path is not None

    def test_nuxt_inherits_from_javascript(self):
        """Nuxt should inherit base quality gates from javascript."""
        config = load_stack("nuxt")

        assert "typecheck" in config.quality_gates
        assert "lint" in config.quality_gates

    def test_nuxt_overrides_tests_gate(self):
        """Nuxt should override tests gate to use vitest."""
        config = load_stack("nuxt")

        assert "tests" in config.quality_gates
        assert "vitest" in config.quality_gates["tests"].command

    def test_nuxt_has_frontend_agents(self):
        """Nuxt should have frontend-* agents."""
        config = load_stack("nuxt")

        agent_names = [a.name for a in config.agents]
        assert "frontend-developer" in agent_names
        assert "frontend-tester" in agent_names
        assert "frontend-reviewer" in agent_names
        assert len(config.agents) == 3

    def test_nuxt_has_own_skills(self):
        """Nuxt should have page, composable, server-route skills."""
        config = load_stack("nuxt")

        assert "new-page" in config.skills
        assert "new-composable" in config.skills
        assert "new-server-route" in config.skills

    def test_nuxt_has_verification(self):
        """Nuxt stack.yaml should have verification section."""
        import yaml

        stack_yaml = Path(__file__).parent.parent / "stacks" / "nuxt" / "stack.yaml"
        with open(stack_yaml) as f:
            raw = yaml.safe_load(f)

        assert "verification" in raw
        assert raw["verification"]["dev_server"]["port"] == 3000

    def test_nuxt_variables(self):
        """Nuxt should have framework-specific variables."""
        config = load_stack("nuxt")

        assert config.variables["framework"] == "Nuxt 3+"
        assert config.variables["language"] == "TypeScript"  # inherited
        assert config.variables["ui_framework"] == "Vue 3"

    def test_validate_nuxt_stack(self):
        """Nuxt stack should pass validation."""
        config = load_stack("nuxt", validate=True)
        assert config.name == "nuxt"


class TestComposeExpress:
    """Tests for composing express with other stacks."""

    def test_compose_express_single(self):
        """compose_stacks(['express']) should work."""
        composed = compose_stacks(["express"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "express"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

    def test_compose_express_with_nextjs(self):
        """Express + nextjs should have 6 agents that coexist."""
        composed = compose_stacks(["express", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names
        assert "frontend-developer" in agent_names
        assert "frontend-tester" in agent_names
        assert "frontend-reviewer" in agent_names
        assert len(composed.all_agents) == 6


class TestComposeNuxt:
    """Tests for composing nuxt with other stacks."""

    def test_compose_nuxt_single(self):
        """compose_stacks(['nuxt']) should work."""
        composed = compose_stacks(["nuxt"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "nuxt"

    def test_compose_nuxt_with_express(self):
        """Nuxt + express should compose successfully."""
        composed = compose_stacks(["nuxt", "express"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "frontend-developer" in agent_names
        assert "backend-developer" in agent_names


class TestRenderExpress:
    """Tests for rendering express stack templates."""

    def test_render_express_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["express"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_express_developer_content(self):
        """Express developer agent should contain Express-specific content."""
        composed = compose_stacks(["express"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Express" in dev_content


class TestRenderNuxt:
    """Tests for rendering nuxt stack templates."""

    def test_render_nuxt_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["nuxt"])
        output = render_all(composed)

        assert "frontend-developer.md" in output.agents
        assert "frontend-tester.md" in output.agents
        assert "frontend-reviewer.md" in output.agents

    def test_render_nuxt_developer_content(self):
        """Nuxt developer agent should contain Nuxt-specific content."""
        composed = compose_stacks(["nuxt"])
        output = render_all(composed)

        dev_content = output.agents["frontend-developer.md"]
        assert "Nuxt" in dev_content

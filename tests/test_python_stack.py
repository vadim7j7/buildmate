"""Tests for the python, flask, fastapi, and django stacks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import (
    compose_stacks,
    load_stack,
)
from lib.renderer import render_all


class TestLoadPythonStack:
    """Tests for loading the python stack."""

    def test_load_python_stack(self):
        """Should load python stack with expected agents, gates, and patterns."""
        config = load_stack("python")

        assert config.name == "python"
        assert config.display_name == "Python"
        assert config.extends is None

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names
        assert len(config.agents) == 3

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "typecheck" in config.quality_gates
        assert "tests" in config.quality_gates

        assert "patterns/backend-patterns.md" in config.patterns
        assert "styles/backend-python.md" in config.styles

    def test_python_stack_variables(self):
        """Python stack should have expected variables."""
        config = load_stack("python")

        assert config.variables["framework"] == "Python"
        assert config.variables["language"] == "Python 3.12+"
        assert config.variables["test_framework"] == "pytest"
        assert config.variables["package_manager"] == "uv"

    def test_python_stack_options(self):
        """Python stack should have db option."""
        config = load_stack("python")

        assert "db" in config.options
        db_option = config.options["db"]
        assert db_option.default == "postgresql"
        assert "postgresql" in db_option.choices
        assert "sqlite" in db_option.choices
        assert "mongodb" in db_option.choices

    def test_python_stack_skills(self):
        """Python stack should have expected skills."""
        config = load_stack("python")

        expected_skills = [
            "test", "review", "docs", "verify",
            "new-model", "new-schema", "new-service",
            "new-test", "new-migration", "db-migrate",
        ]
        for skill in expected_skills:
            assert skill in config.skills

    def test_validate_python_stack(self):
        """Python stack should pass validation."""
        # load_stack validates by default — no exception means pass
        config = load_stack("python", validate=True)
        assert config.name == "python"


class TestLoadFlaskStack:
    """Tests for loading the flask stack with inheritance."""

    def test_load_flask_stack(self):
        """Should load flask stack with extends resolved."""
        config = load_stack("flask")

        assert config.name == "flask"
        assert config.display_name == "Flask Web Application"
        assert config.parent_stack_path is not None

    def test_flask_inherits_python_quality_gates(self):
        """Flask should inherit all quality gates from python."""
        config = load_stack("flask")

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "typecheck" in config.quality_gates
        assert "tests" in config.quality_gates
        assert config.quality_gates["format"].command == "uv run ruff format --check src/ tests/"

    def test_flask_inherits_python_tester_agent(self):
        """Flask should have its own backend-tester and backend-reviewer."""
        config = load_stack("flask")

        agent_names = [a.name for a in config.agents]
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

        # Verify tester comes from flask (overrides python parent)
        tester = next(a for a in config.agents if a.name == "backend-tester")
        assert tester.source_stack == "flask"

    def test_flask_overrides_developer_agent(self):
        """Flask's backend-developer should replace python's."""
        config = load_stack("flask")

        dev = next(a for a in config.agents if a.name == "backend-developer")
        assert dev.source_stack == "flask"
        assert "new-blueprint" in dev.skills

    def test_flask_inherits_db_option(self):
        """Flask should have db option inherited from python."""
        config = load_stack("flask")

        assert "db" in config.options
        db_option = config.options["db"]
        assert db_option.default == "postgresql"
        assert "postgresql" in db_option.choices

    def test_flask_has_own_skills(self):
        """Flask should have new-blueprint and new-route skills."""
        config = load_stack("flask")

        assert "new-blueprint" in config.skills
        assert "new-route" in config.skills

    def test_flask_has_inherited_skills(self):
        """Flask should also have skills inherited from python."""
        config = load_stack("flask")

        assert "test" in config.skills
        assert "review" in config.skills
        assert "new-model" in config.skills

    def test_flask_has_verification(self):
        """Flask stack.yaml should have verification section."""
        import yaml

        stack_yaml = Path(__file__).parent.parent / "stacks" / "flask" / "stack.yaml"
        with open(stack_yaml) as f:
            raw = yaml.safe_load(f)

        assert "verification" in raw
        assert raw["verification"]["enabled"] is True
        assert raw["verification"]["dev_server"]["port"] == 5000

    def test_flask_patterns_merged(self):
        """Both python and flask patterns should be present."""
        config = load_stack("flask")

        assert "patterns/backend-patterns.md" in config.patterns
        assert "patterns/flask-patterns.md" in config.patterns

    def test_flask_variables_override(self):
        """Flask should override framework but inherit language."""
        config = load_stack("flask")

        assert config.variables["framework"] == "Flask 3+"
        assert config.variables["language"] == "Python 3.12+"
        assert config.variables["test_framework"] == "pytest"
        assert config.variables["dev_port"] == 5000

    def test_flask_compatible_with(self):
        """Flask compatible_with should be union of python + flask."""
        config = load_stack("flask")

        assert "nextjs" in config.compatible_with
        assert "react-native" in config.compatible_with

    def test_validate_flask_stack(self):
        """Flask stack should pass validation."""
        config = load_stack("flask", validate=True)
        assert config.name == "flask"


class TestComposeFlask:
    """Tests for composing flask with other stacks."""

    def test_compose_flask_single(self):
        """compose_stacks(['flask']) should work."""
        composed = compose_stacks(["flask"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "flask"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

    def test_compose_flask_has_quality_gates(self):
        """Composed flask should have quality gates under flask key."""
        composed = compose_stacks(["flask"])

        assert "flask" in composed.all_quality_gates
        gates = composed.all_quality_gates["flask"]
        assert "format" in gates
        assert "lint" in gates
        assert "typecheck" in gates
        assert "tests" in gates

    def test_compose_flask_with_nextjs(self):
        """Flask + nextjs multi-stack composition should work."""
        composed = compose_stacks(["flask", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names

        assert "flask" in composed.all_quality_gates
        assert "nextjs" in composed.all_quality_gates

    def test_compose_flask_patterns_collected(self):
        """Composed flask should collect both python and flask patterns."""
        composed = compose_stacks(["flask"])

        pattern_names = list(composed.all_patterns.keys())
        assert "backend-patterns.md" in pattern_names
        assert "flask-patterns.md" in pattern_names

    def test_compose_flask_styles_collected(self):
        """Composed flask should collect python styles."""
        composed = compose_stacks(["flask"])

        style_names = list(composed.all_styles.keys())
        assert "backend-python.md" in style_names

    def test_compose_flask_skills_merged(self):
        """Composed flask should have both inherited and own skills."""
        composed = compose_stacks(["flask"])

        assert "test" in composed.all_skills
        assert "new-blueprint" in composed.all_skills
        assert "new-route" in composed.all_skills
        assert "new-model" in composed.all_skills

    def test_compose_python_single(self):
        """compose_stacks(['python']) should work standalone."""
        composed = compose_stacks(["python"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "python"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names


class TestRenderFlaskStack:
    """Tests for rendering flask stack templates."""

    def test_render_flask_stack(self):
        """Full render should produce expected agents, patterns, and skills."""
        composed = compose_stacks(["flask"])
        output = render_all(composed)

        # Should have base agents + stack agents
        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

        # Patterns and styles should be collected
        assert "backend-patterns.md" in output.patterns
        assert "flask-patterns.md" in output.patterns
        assert "backend-python.md" in output.styles

        # Skills should include both inherited and flask-specific
        assert "new-blueprint" in output.skills
        assert "new-route" in output.skills

    def test_render_flask_developer_content(self):
        """Flask developer agent should contain Flask-specific content."""
        composed = compose_stacks(["flask"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Flask" in dev_content
        assert "blueprint" in dev_content.lower()

    def test_render_flask_tester_content(self):
        """Flask tester agent (inherited) should contain pytest content."""
        composed = compose_stacks(["flask"])
        output = render_all(composed)

        tester_content = output.agents["backend-tester.md"]
        assert "pytest" in tester_content.lower()

    def test_render_python_stack(self):
        """Render python stack standalone should work."""
        composed = compose_stacks(["python"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents
        assert "backend-patterns.md" in output.patterns
        assert "backend-python.md" in output.styles


class TestLoadFastapiRefactored:
    """Tests for loading the refactored fastapi stack with extends: python."""

    def test_load_fastapi_stack(self):
        """Should load fastapi stack with extends resolved."""
        config = load_stack("fastapi")

        assert config.name == "fastapi"
        assert config.display_name == "Python FastAPI"
        assert config.parent_stack_path is not None

    def test_fastapi_inherits_quality_gates(self):
        """FastAPI should inherit quality gates from python."""
        config = load_stack("fastapi")

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "typecheck" in config.quality_gates
        assert "tests" in config.quality_gates

    def test_fastapi_inherits_styles(self):
        """FastAPI should inherit styles from python parent."""
        config = load_stack("fastapi")

        assert "styles/backend-python.md" in config.styles

    def test_fastapi_overrides_all_agents(self):
        """FastAPI should override all 3 agents from python parent."""
        config = load_stack("fastapi")

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names
        assert len(config.agents) == 3

        # All agents should be sourced from fastapi
        for agent in config.agents:
            assert agent.source_stack == "fastapi"

    def test_fastapi_has_own_patterns(self):
        """FastAPI should have fastapi-patterns.md (not backend-patterns.md collision)."""
        config = load_stack("fastapi")

        assert "patterns/fastapi-patterns.md" in config.patterns
        # Also inherits python parent pattern
        assert "patterns/backend-patterns.md" in config.patterns

    def test_fastapi_has_own_skills(self):
        """FastAPI should have its own skills plus inherited ones."""
        config = load_stack("fastapi")

        # FastAPI-specific
        assert "new-router" in config.skills
        assert "new-dependency" in config.skills
        assert "new-middleware" in config.skills
        # Inherited from python
        assert "test" in config.skills
        assert "review" in config.skills

    def test_fastapi_variables_override(self):
        """FastAPI should override framework but inherit language."""
        config = load_stack("fastapi")

        assert config.variables["framework"] == "FastAPI"
        assert config.variables["language"] == "Python 3.12+"
        assert "pytest" in config.variables["test_framework"]

    def test_fastapi_inherits_db_option(self):
        """FastAPI should have db option inherited from python."""
        config = load_stack("fastapi")

        assert "db" in config.options
        db_option = config.options["db"]
        assert db_option.default == "postgresql"
        assert "postgresql" in db_option.choices

    def test_validate_fastapi_stack(self):
        """FastAPI stack should pass validation."""
        config = load_stack("fastapi", validate=True)
        assert config.name == "fastapi"


class TestLoadDjango:
    """Tests for loading the django stack with extends: python."""

    def test_load_django_stack(self):
        """Should load django stack with extends resolved."""
        config = load_stack("django")

        assert config.name == "django"
        assert config.display_name == "Django Web Application"
        assert config.parent_stack_path is not None

    def test_django_inherits_from_python(self):
        """Django should inherit quality gates and styles from python."""
        config = load_stack("django")

        assert "format" in config.quality_gates
        assert "lint" in config.quality_gates
        assert "typecheck" in config.quality_gates
        assert "tests" in config.quality_gates
        assert "styles/backend-python.md" in config.styles

    def test_django_overrides_developer_agent(self):
        """Django should override all three agents with its own."""
        config = load_stack("django")

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

        dev = next(a for a in config.agents if a.name == "backend-developer")
        assert dev.source_stack == "django"

        tester = next(a for a in config.agents if a.name == "backend-tester")
        assert tester.source_stack == "django"

    def test_django_has_own_skills(self):
        """Django should have new-view, new-serializer, new-url-config skills."""
        config = load_stack("django")

        assert "new-view" in config.skills
        assert "new-serializer" in config.skills
        assert "new-url-config" in config.skills
        # Also inherited
        assert "test" in config.skills
        assert "review" in config.skills

    def test_django_has_verification(self):
        """Django stack.yaml should have verification section."""
        import yaml

        stack_yaml = Path(__file__).parent.parent / "stacks" / "django" / "stack.yaml"
        with open(stack_yaml) as f:
            raw = yaml.safe_load(f)

        assert "verification" in raw
        assert raw["verification"]["dev_server"]["port"] == 8000

    def test_django_variables(self):
        """Django should have framework-specific variables."""
        config = load_stack("django")

        assert config.variables["framework"] == "Django 5+"
        assert config.variables["language"] == "Python 3.12+"  # inherited
        assert config.variables["orm"] == "Django ORM"

    def test_django_inherits_db_option(self):
        """Django should have db option inherited from python."""
        config = load_stack("django")

        assert "db" in config.options
        db_option = config.options["db"]
        assert db_option.default == "postgresql"
        assert "postgresql" in db_option.choices

    def test_django_patterns_merged(self):
        """Both python and django patterns should be present."""
        config = load_stack("django")

        # Python parent pattern
        assert "patterns/backend-patterns.md" in config.patterns
        # Django-specific patterns
        assert "patterns/django-patterns.md" in config.patterns

    def test_validate_django_stack(self):
        """Django stack should pass validation."""
        config = load_stack("django", validate=True)
        assert config.name == "django"


class TestComposeFastapi:
    """Tests for composing fastapi with other stacks."""

    def test_compose_fastapi_single(self):
        """compose_stacks(['fastapi']) should work."""
        composed = compose_stacks(["fastapi"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "fastapi"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

    def test_compose_fastapi_with_nextjs(self):
        """FastAPI + nextjs multi-stack composition should work."""
        composed = compose_stacks(["fastapi", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names

        assert "fastapi" in composed.all_quality_gates
        assert "nextjs" in composed.all_quality_gates


class TestComposeDjango:
    """Tests for composing django with other stacks."""

    def test_compose_django_single(self):
        """compose_stacks(['django']) should work."""
        composed = compose_stacks(["django"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "django"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

    def test_compose_django_with_nextjs(self):
        """Django + nextjs multi-stack composition should work."""
        composed = compose_stacks(["django", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names

        assert "django" in composed.all_quality_gates
        assert "nextjs" in composed.all_quality_gates


class TestRenderFastapi:
    """Tests for rendering fastapi stack templates."""

    def test_render_fastapi_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["fastapi"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_fastapi_developer_content(self):
        """FastAPI developer agent should contain FastAPI-specific content."""
        composed = compose_stacks(["fastapi"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "FastAPI" in dev_content


class TestRenderDjango:
    """Tests for rendering django stack templates."""

    def test_render_django_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["django"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_django_developer_content(self):
        """Django developer agent should contain Django-specific content."""
        composed = compose_stacks(["django"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Django" in dev_content

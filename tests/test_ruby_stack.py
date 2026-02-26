"""Tests for the ruby, rails, and sinatra stacks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import (
    compose_stacks,
    load_stack,
)
from lib.renderer import render_all


class TestLoadRubyStack:
    """Tests for loading the ruby parent stack."""

    def test_load_ruby_stack(self):
        """Should load ruby stack with expected agents, gates, and patterns."""
        config = load_stack("ruby")

        assert config.name == "ruby"
        assert config.display_name == "Ruby"
        assert config.extends is None

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names
        assert len(config.agents) == 3

        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates

        assert "patterns/backend-patterns.md" in config.patterns
        assert "styles/backend-ruby.md" in config.styles

    def test_ruby_stack_variables(self):
        """Ruby stack should have expected variables."""
        config = load_stack("ruby")

        assert config.variables["framework"] == "Ruby"
        assert config.variables["language"] == "Ruby 3.2+"
        assert config.variables["test_framework"] == "RSpec"
        assert config.variables["orm"] == "Sequel"

    def test_ruby_stack_options(self):
        """Ruby stack should have db option."""
        config = load_stack("ruby")

        assert "db" in config.options
        db_option = config.options["db"]
        assert db_option.default == "postgresql"
        assert "postgresql" in db_option.choices
        assert "mysql" in db_option.choices
        assert "sqlite" in db_option.choices
        assert "mongodb" in db_option.choices

    def test_ruby_stack_skills(self):
        """Ruby stack should have expected skills."""
        config = load_stack("ruby")

        expected_skills = ["test", "review", "docs", "verify", "new-model", "new-service", "new-spec"]
        for skill in expected_skills:
            assert skill in config.skills

    def test_validate_ruby_stack(self):
        """Ruby stack should pass validation."""
        config = load_stack("ruby", validate=True)
        assert config.name == "ruby"


class TestLoadRailsRefactored:
    """Tests for loading the refactored rails stack with extends: ruby."""

    def test_load_rails_stack(self):
        """Should load rails stack with extends resolved."""
        config = load_stack("rails")

        assert config.name == "rails"
        assert config.display_name == "Ruby on Rails API"
        assert config.parent_stack_path is not None

    def test_rails_inherits_quality_gates(self):
        """Rails should inherit quality gates from ruby."""
        config = load_stack("rails")

        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates
        assert config.quality_gates["lint"].command == "bundle exec rubocop"

    def test_rails_inherits_styles(self):
        """Rails should inherit styles from ruby parent."""
        config = load_stack("rails")

        assert "styles/backend-ruby.md" in config.styles

    def test_rails_overrides_all_agents(self):
        """Rails should override all 3 agents from ruby parent."""
        config = load_stack("rails")

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names
        assert len(config.agents) == 3

        # All agents should be sourced from rails
        for agent in config.agents:
            assert agent.source_stack == "rails"

    def test_rails_has_own_skills(self):
        """Rails should have its own skills plus inherited ones."""
        config = load_stack("rails")

        # Rails-specific
        assert "new-controller" in config.skills
        assert "new-presenter" in config.skills
        assert "new-job" in config.skills
        assert "db-migrate" in config.skills
        # Inherited from ruby
        assert "test" in config.skills
        assert "review" in config.skills

    def test_rails_has_own_options(self):
        """Rails should have jobs, serializer options plus inherited db."""
        config = load_stack("rails")

        assert "jobs" in config.options
        assert "serializer" in config.options
        assert "db" in config.options  # inherited from ruby

    def test_rails_patterns_merged(self):
        """Both ruby and rails patterns should be present."""
        config = load_stack("rails")

        # Ruby parent pattern
        assert "patterns/backend-patterns.md" in config.patterns
        # Rails-specific patterns
        assert "patterns/auth.md" in config.patterns
        assert "patterns/pagination.md" in config.patterns

    def test_rails_variables_override(self):
        """Rails should override framework but inherit language."""
        config = load_stack("rails")

        assert config.variables["framework"] == "Rails 7+"
        assert config.variables["language"] == "Ruby"
        assert config.variables["orm"] == "ActiveRecord"
        assert config.variables["test_framework"] == "RSpec"

    def test_validate_rails_stack(self):
        """Rails stack should pass validation."""
        config = load_stack("rails", validate=True)
        assert config.name == "rails"


class TestLoadSinatra:
    """Tests for loading the sinatra stack with extends: ruby."""

    def test_load_sinatra_stack(self):
        """Should load sinatra stack with extends resolved."""
        config = load_stack("sinatra")

        assert config.name == "sinatra"
        assert config.display_name == "Sinatra Web Application"
        assert config.parent_stack_path is not None

    def test_sinatra_inherits_from_ruby(self):
        """Sinatra should inherit quality gates and styles from ruby."""
        config = load_stack("sinatra")

        assert "lint" in config.quality_gates
        assert "tests" in config.quality_gates
        assert "styles/backend-ruby.md" in config.styles

    def test_sinatra_overrides_developer_agent(self):
        """Sinatra should override backend-developer but inherit tester and reviewer."""
        config = load_stack("sinatra")

        agent_names = [a.name for a in config.agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

        dev = next(a for a in config.agents if a.name == "backend-developer")
        assert dev.source_stack == "sinatra"

        tester = next(a for a in config.agents if a.name == "backend-tester")
        assert tester.source_stack == "ruby"

    def test_sinatra_has_own_skills(self):
        """Sinatra should have new-route and new-helper skills."""
        config = load_stack("sinatra")

        assert "new-route" in config.skills
        assert "new-helper" in config.skills
        # Also inherited
        assert "test" in config.skills
        assert "review" in config.skills

    def test_sinatra_has_verification(self):
        """Sinatra stack.yaml should have verification section."""
        import yaml

        stack_yaml = Path(__file__).parent.parent / "stacks" / "sinatra" / "stack.yaml"
        with open(stack_yaml) as f:
            raw = yaml.safe_load(f)

        assert "verification" in raw
        assert raw["verification"]["enabled"] is True
        assert raw["verification"]["dev_server"]["port"] == 4567

    def test_sinatra_variables(self):
        """Sinatra should override framework but inherit language from ruby."""
        config = load_stack("sinatra")

        assert config.variables["framework"] == "Sinatra 4+"
        assert config.variables["language"] == "Ruby 3.2+"
        assert config.variables["test_framework"] == "RSpec"

    def test_validate_sinatra_stack(self):
        """Sinatra stack should pass validation."""
        config = load_stack("sinatra", validate=True)
        assert config.name == "sinatra"


class TestComposeRails:
    """Tests for composing rails with other stacks."""

    def test_compose_rails_single(self):
        """compose_stacks(['rails']) should work."""
        composed = compose_stacks(["rails"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "rails"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

    def test_compose_rails_with_nextjs(self):
        """Rails + nextjs multi-stack composition should work."""
        composed = compose_stacks(["rails", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names

        assert "rails" in composed.all_quality_gates
        assert "nextjs" in composed.all_quality_gates


class TestComposeSinatra:
    """Tests for composing sinatra with other stacks."""

    def test_compose_sinatra_single(self):
        """compose_stacks(['sinatra']) should work."""
        composed = compose_stacks(["sinatra"])

        assert len(composed.stacks) == 1
        assert composed.stacks[0].name == "sinatra"

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "backend-tester" in agent_names
        assert "backend-reviewer" in agent_names

    def test_compose_sinatra_with_nextjs(self):
        """Sinatra + nextjs multi-stack composition should work."""
        composed = compose_stacks(["sinatra", "nextjs"])

        assert len(composed.stacks) == 2

        agent_names = [a.name for a in composed.all_agents]
        assert "backend-developer" in agent_names
        assert "frontend-developer" in agent_names


class TestRenderRails:
    """Tests for rendering rails stack templates."""

    def test_render_rails_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_rails_developer_content(self):
        """Rails developer agent should contain Rails-specific content."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Rails" in dev_content


class TestRenderSinatra:
    """Tests for rendering sinatra stack templates."""

    def test_render_sinatra_stack(self):
        """Full render should produce expected agents."""
        composed = compose_stacks(["sinatra"])
        output = render_all(composed)

        assert "backend-developer.md" in output.agents
        assert "backend-tester.md" in output.agents
        assert "backend-reviewer.md" in output.agents

    def test_render_sinatra_developer_content(self):
        """Sinatra developer agent should contain Sinatra-specific content."""
        composed = compose_stacks(["sinatra"])
        output = render_all(composed)

        dev_content = output.agents["backend-developer.md"]
        assert "Sinatra" in dev_content

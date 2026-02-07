"""Tests for schema validation module."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.schema import check_agent_conflicts, check_compatibility, validate_stack_config


class TestValidateStackConfig:
    """Tests for validate_stack_config function."""

    def test_valid_minimal_config(self):
        """Valid minimal config should pass validation."""
        config = {
            "name": "test-stack",
            "display_name": "Test Stack",
            "agents": [
                {
                    "name": "test-agent",
                    "template": "agents/test.md.j2",
                    "tools": ["Read", "Write"],
                }
            ],
            "skills": ["test"],
            "quality_gates": {
                "lint": {
                    "command": "npm run lint",
                }
            },
        }
        # Should not raise
        validate_stack_config(config)

    def test_valid_full_config(self):
        """Valid full config with all optional fields should pass."""
        config = {
            "name": "test-stack",
            "display_name": "Test Stack",
            "description": "A test stack",
            "default_model": "opus",
            "compatible_with": ["rails", "nextjs"],
            "agents": [
                {
                    "name": "test-agent",
                    "template": "agents/test.md.j2",
                    "description": "Test agent",
                    "tools": ["Read", "Write", "Edit"],
                    "model": "sonnet",
                }
            ],
            "skills": ["test", "review"],
            "quality_gates": {
                "lint": {
                    "command": "npm run lint",
                    "fix_command": "npm run lint --fix",
                    "description": "Linting",
                },
                "tests": {
                    "command": "npm test",
                },
            },
            "working_dir": ".",
            "patterns": ["patterns/test.md"],
            "styles": ["styles/test.md"],
            "variables": {
                "framework": "Test Framework",
                "language": "TypeScript",
            },
        }
        validate_stack_config(config)

    def test_missing_required_name(self):
        """Config missing name should fail validation."""
        config = {
            "display_name": "Test Stack",
            "agents": [],
            "skills": [],
            "quality_gates": {},
        }
        with pytest.raises(Exception):
            validate_stack_config(config)

    def test_missing_required_agents(self):
        """Config missing agents should fail validation."""
        config = {
            "name": "test-stack",
            "display_name": "Test Stack",
            "skills": [],
            "quality_gates": {},
        }
        with pytest.raises(Exception):
            validate_stack_config(config)

    def test_agent_missing_required_name(self):
        """Agent missing name should fail validation."""
        config = {
            "name": "test-stack",
            "display_name": "Test Stack",
            "agents": [
                {
                    "template": "agents/test.md.j2",
                    "tools": ["Read"],
                }
            ],
            "skills": [],
            "quality_gates": {},
        }
        with pytest.raises(Exception):
            validate_stack_config(config)

    def test_agent_missing_required_template(self):
        """Agent missing template should fail validation."""
        config = {
            "name": "test-stack",
            "display_name": "Test Stack",
            "agents": [
                {
                    "name": "test-agent",
                    "tools": ["Read"],
                }
            ],
            "skills": [],
            "quality_gates": {},
        }
        with pytest.raises(Exception):
            validate_stack_config(config)

    def test_quality_gate_missing_command(self):
        """Quality gate missing command should fail validation."""
        config = {
            "name": "test-stack",
            "display_name": "Test Stack",
            "agents": [
                {
                    "name": "test-agent",
                    "template": "agents/test.md.j2",
                    "tools": ["Read"],
                }
            ],
            "skills": [],
            "quality_gates": {
                "lint": {
                    "description": "No command",
                }
            },
        }
        with pytest.raises(Exception):
            validate_stack_config(config)


class TestCheckCompatibility:
    """Tests for check_compatibility function."""

    def test_compatible_stacks(self):
        """Compatible stacks should return no warnings."""
        configs = [
            {"name": "rails", "compatible_with": ["nextjs"]},
            {"name": "nextjs", "compatible_with": ["rails"]},
        ]
        warnings = check_compatibility(configs)
        assert len(warnings) == 0

    def test_incompatible_stacks(self):
        """Incompatible stacks should return warnings."""
        configs = [
            {"name": "rails", "compatible_with": ["nextjs"]},
            {"name": "fastapi", "compatible_with": ["nextjs"]},
        ]
        warnings = check_compatibility(configs)
        assert len(warnings) > 0
        assert any("rails" in w and "fastapi" in w for w in warnings)

    def test_single_stack_no_warnings(self):
        """Single stack should return no warnings."""
        configs = [
            {"name": "rails", "compatible_with": ["nextjs"]},
        ]
        warnings = check_compatibility(configs)
        assert len(warnings) == 0

    def test_missing_compatible_with(self):
        """Stack without compatible_with should work."""
        configs = [
            {"name": "rails"},
            {"name": "nextjs"},
        ]
        warnings = check_compatibility(configs)
        # Should have warnings since no compatibility declared
        assert len(warnings) > 0


class TestCheckAgentConflicts:
    """Tests for check_agent_conflicts function."""

    def test_no_conflicts(self):
        """Different agent names should return no warnings."""
        configs = [
            {"name": "rails", "agents": [{"name": "backend-dev"}]},
            {"name": "nextjs", "agents": [{"name": "frontend-dev"}]},
        ]
        warnings = check_agent_conflicts(configs)
        assert len(warnings) == 0

    def test_conflicting_agents(self):
        """Same agent names should return warnings."""
        configs = [
            {"name": "rails", "agents": [{"name": "backend-dev"}]},
            {"name": "fastapi", "agents": [{"name": "backend-dev"}]},
        ]
        warnings = check_agent_conflicts(configs)
        assert len(warnings) > 0
        assert any("backend-dev" in w for w in warnings)

    def test_multiple_conflicts(self):
        """Multiple conflicts should all be reported."""
        configs = [
            {"name": "rails", "agents": [{"name": "dev"}, {"name": "tester"}]},
            {"name": "fastapi", "agents": [{"name": "dev"}, {"name": "tester"}]},
        ]
        warnings = check_agent_conflicts(configs)
        assert len(warnings) >= 2

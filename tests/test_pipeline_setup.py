"""Tests for the generated pipeline setup: /pm workflow, verifiers, hooks, config files."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import STACKS_DIR, compose_stacks, load_stack
from lib.installer import install
from lib.renderer import render_all, verifier_for
from lib.schema import check_compatibility, check_stack_files


def _install(stacks, target, options=None):
    composed = compose_stacks(stacks, options=options or {})
    output = render_all(composed)
    install(output, target, stacks, force=True)
    return output


class TestPmWorkflow:
    """The orchestrator is part of the pm skill, not a spawnable agent."""

    def test_orchestrator_is_a_pm_skill_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _install(["rails", "nextjs"], target)

            assert not (target / ".claude/agents/orchestrator.md").exists()
            workflow = target / ".claude/skills/pm/orchestrator.md"
            assert workflow.exists()
            # Templates are rendered, not copied
            assert not (target / ".claude/skills/pm/orchestrator.md.j2").exists()
            assert "{%" not in workflow.read_text()

    def test_delegations_name_the_agent(self):
        output = render_all(compose_stacks(["rails", "nextjs"]))
        workflow = output.skill_files["pm/orchestrator.md"]

        assert "general-purpose" not in workflow
        for agent in (
            "backend-developer",
            "frontend-tester",
            "backend-reviewer",
            "grind",
        ):
            assert f'subagent_type: "{agent}"' in workflow

    def test_grind_gates_have_no_extra_cd(self):
        """Gate commands already cd into the working dir; no bare `cd dir` lines."""
        output = render_all(compose_stacks(["rails", "nextjs"]))
        workflow = output.skill_files["pm/orchestrator.md"]

        lines = [line.strip() for line in workflow.splitlines()]
        assert "cd backend" not in lines
        assert "- cd backend && bundle exec rubocop" in lines

    def test_no_kill_by_port(self):
        output = render_all(compose_stacks(["rails", "nextjs"]))
        texts = [output.skill_files["pm/orchestrator.md"]] + [
            output.agents[name]
            for name in output.agents
            if name.endswith("-verifier.md")
        ]
        for text in texts:
            assert "xargs kill -9" not in text

    def test_base_agents_listed_with_descriptions(self):
        output = render_all(compose_stacks(["rails"]))
        workflow = output.skill_files["pm/orchestrator.md"]

        assert "| `grind` | Fix-verify loop agent. |" in workflow


class TestVerifiers:
    def test_verifier_by_developer_role(self):
        assert verifier_for(load_stack("rails")) == "backend-verifier"
        assert verifier_for(load_stack("nextjs")) == "frontend-verifier"
        assert verifier_for(load_stack("react-native")) == "mobile-verifier"
        assert verifier_for(load_stack("browser-extension")) is None

    def test_only_used_verifiers_installed(self):
        output = render_all(compose_stacks(["rails", "nextjs"]))

        assert "backend-verifier.md" in output.agents
        assert "frontend-verifier.md" in output.agents
        assert "mobile-verifier.md" not in output.agents

    def test_verifier_uses_stack_dev_server(self):
        output = render_all(compose_stacks(["rails", "nextjs"]))
        backend = output.agents["backend-verifier.md"]

        assert "bundle exec rails server -p 3001" in backend
        assert "PORT=3001" in backend
        assert "/health" in backend


class TestOptionSkills:
    def test_option_injected_skill_is_installed(self):
        """nextjs state=zustand adds new-store only through the option."""
        output = render_all(
            compose_stacks(["nextjs"], options={"nextjs": {"state": "zustand"}})
        )
        assert "new-store" in output.skills


class TestBuildmateConfig:
    def test_written_outside_claude_settings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _install(["rails"], target)

            settings = json.loads((target / ".claude/settings.json").read_text())
            config = json.loads((target / ".claude/buildmate.json").read_text())
            assert "pm" not in settings
            assert config["pm"]["git_workflow"] == "none"

    def test_user_choice_kept_on_reinstall(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _install(["rails"], target)
            path = target / ".claude/buildmate.json"
            config = json.loads(path.read_text())
            config["pm"]["git_workflow"] = "branch"
            path.write_text(json.dumps(config))

            _install(["rails"], target)

            assert json.loads(path.read_text())["pm"]["git_workflow"] == "branch"

    def test_legacy_pm_settings_migrated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            (target / ".claude").mkdir()
            (target / ".claude/settings.json").write_text(
                json.dumps({"pm": {"git_workflow": "full"}})
            )

            _install(["rails"], target)

            config = json.loads((target / ".claude/buildmate.json").read_text())
            assert config["pm"]["git_workflow"] == "full"


class TestSettings:
    def _settings(self):
        return render_all(compose_stacks(["rails"])).settings

    def test_session_hooks_wired(self):
        hooks = self._settings()["hooks"]
        assert "SessionStart" in hooks
        assert "SessionEnd" in hooks
        assert "Stop" not in hooks
        commands = [
            h["command"] for event in hooks.values() for m in event for h in m["hooks"]
        ]
        assert all(
            c.startswith('"$CLAUDE_PROJECT_DIR"/.claude/hooks/') for c in commands
        )

    def test_hook_scripts_exist(self):
        output = render_all(compose_stacks(["rails"]))
        hooks = output.settings["hooks"]
        for event in hooks.values():
            for matcher in event:
                for hook in matcher["hooks"]:
                    script = hook["command"].rsplit("/", 1)[-1]
                    assert script in output.hook_files, script

    def test_destructive_git_denied(self):
        deny = self._settings()["permissions"]["deny"]
        assert "Bash(git push --force*)" in deny
        assert "Bash(gh pr merge*)" in deny


class TestCompatibility:
    def test_either_side_declaring_is_enough(self):
        configs = [
            {"name": "a", "compatible_with": ["b"]},
            {"name": "b", "compatible_with": []},
        ]
        assert check_compatibility(configs) == []

    def test_parent_declaration_covers_child(self):
        configs = [
            {"name": "scraping", "compatible_with": ["python"]},
            {"name": "django", "extends": "python", "compatible_with": []},
        ]
        assert check_compatibility(configs) == []

    def test_real_combinations(self):
        for combo in (
            ["django", "scraping"],
            ["flask", "scraping"],
            ["nuxt", "browser-extension"],
        ):
            compose_stacks(combo)  # raises on incompatibility


class TestStackFiles:
    def test_missing_referenced_pattern_is_error(self, tmp_path):
        stack = tmp_path / "stacks" / "demo"
        stack.mkdir(parents=True)
        errors, _ = check_stack_files(
            stack, {"name": "demo", "patterns": ["patterns/x.md"]}
        )
        assert errors == ["Referenced file not found: patterns/x.md"]

    def test_unreferenced_pattern_is_warning(self, tmp_path):
        stack = tmp_path / "stacks" / "demo"
        (stack / "patterns").mkdir(parents=True)
        (stack / "patterns" / "extra.md").write_text("x")
        errors, warnings = check_stack_files(stack, {"name": "demo"})
        assert errors == []
        assert warnings == ["Unreferenced file: patterns/extra.md"]

    def test_all_stacks_have_no_missing_files(self):
        import yaml

        for stack_dir in sorted(STACKS_DIR.iterdir()):
            stack_yaml = stack_dir / "stack.yaml"
            if stack_yaml.exists():
                errors, _ = check_stack_files(
                    stack_dir, yaml.safe_load(stack_yaml.read_text())
                )
                assert errors == [], (stack_dir.name, errors)

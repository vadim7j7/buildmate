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


class TestPerStackContext:
    """Each stack's agents and skills see that stack's own variables."""

    def test_backend_agents_do_not_get_frontend_variables(self):
        output = render_all(compose_stacks(["rails", "nextjs"]))
        backend = output.agents["backend-developer.md"]
        frontend = output.agents["frontend-developer.md"]

        assert "Rails 8+" in backend
        assert "Next.js (App Router)" not in backend
        assert "Next.js" in frontend

    def test_option_variables_reach_the_stack(self):
        composed = compose_stacks(["nextjs"], options={"nextjs": {"ui": "tailwind"}})
        nextjs = composed.stacks[0]

        assert any("tailwind" in style for style in nextjs.styles)

    def test_skill_template_uses_its_stack(self, tmp_path, monkeypatch):
        """A SKILL.md.j2 in a stack is rendered with that stack's variables."""
        from lib import renderer

        skill_dir = STACKS_DIR / "rails" / "skills" / "_tmp-template-skill"
        skill_dir.mkdir()
        try:
            (skill_dir / "SKILL.md.j2").write_text(
                "framework={{ variables.framework }}"
            )
            composed = compose_stacks(["rails", "nextjs"])
            env = renderer.create_jinja_env([renderer.V2_ROOT])
            context = renderer.build_template_context(composed)
            files = renderer.render_skill_templates(
                env, context, {"_tmp-template-skill": skill_dir}, composed.stacks
            )
            assert files["_tmp-template-skill/SKILL.md"] == "framework=Rails 8+"
        finally:
            for f in skill_dir.iterdir():
                f.unlink()
            skill_dir.rmdir()


class TestPatternInstall:
    def test_base_patterns_installed(self):
        output = render_all(compose_stacks(["fastapi"]))
        assert "git-workflow.md" in output.patterns
        assert "browser-cloning.md" in output.patterns

    def test_reference_patterns_installed_and_listed(self):
        composed = compose_stacks(["rails"])
        rails = composed.stacks[0]
        if not rails.reference_patterns:
            return  # nothing to check until the stack declares some
        output = render_all(composed)
        name = Path(rails.reference_patterns[0]).name
        assert name in output.patterns
        assert f".claude/patterns/{name}" in output.agents["backend-developer.md"]

    def test_skill_template_counts_as_skill_file(self, tmp_path):
        stack = tmp_path / "stacks" / "demo"
        (stack / "skills" / "x").mkdir(parents=True)
        (stack / "skills" / "x" / "SKILL.md.j2").write_text("x")
        errors, _ = check_stack_files(stack, {"name": "demo", "skills": ["x"]})
        assert errors == []


class TestRenderedReferences:
    """Everything the generated setup tells Claude to use must be installed."""

    @staticmethod
    def _outputs(with_config=False):
        from lib.config import (
            list_available_profiles,
            list_available_stacks,
            load_profile,
        )

        configs = [(name, compose_stacks([name])) for name in list_available_stacks()]
        for name in list_available_profiles():
            profile = load_profile(name)
            configs.append(
                (
                    name,
                    compose_stacks(
                        profile.stacks, options=profile.options, profile=profile
                    ),
                )
            )
        for name, composed in configs:
            output = render_all(composed)
            yield (name, output, composed) if with_config else (name, output)

    def test_subagent_types_exist(self):
        import re

        pattern = re.compile(r'subagent_type: "([a-z0-9-]+)"')
        for name, output in self._outputs():
            installed = {f[:-3] for f in output.agents}
            texts = list(output.skill_files.values()) + [output.claude_md]
            for text in texts:
                for agent in pattern.findall(text):
                    assert agent in installed, (name, agent)

    def test_pattern_and_style_paths_exist(self):
        import re

        pattern = re.compile(r"\.claude/(patterns|styles)/([A-Za-z0-9_.-]+\.md)")
        for name, output, composed in self._outputs(with_config=True):
            installed = {"patterns": set(output.patterns), "styles": set(output.styles)}
            # Skills copied as-is may say "if you chose X, read <X's pattern>"
            for stack in composed.stacks:
                for option in stack.options.values():
                    for choice in option.choices.values():
                        installed["patterns"] |= {Path(f).name for f in choice.patterns}
                        installed["styles"] |= {Path(f).name for f in choice.styles}
            texts = list(output.agents.values()) + list(output.skill_files.values())
            for skill_dir in output.skills.values():
                texts += [f.read_text() for f in skill_dir.rglob("*.md")]
            for text in texts:
                for kind, filename in pattern.findall(text):
                    assert filename in installed[kind], (name, kind, filename)


class TestNameCollisions:
    """Same-named files from two stacks must not replace each other."""

    def test_both_testing_patterns_installed(self):
        composed = compose_stacks(["rails", "nextjs"])
        output = render_all(composed)

        assert "rails-testing.md" in output.patterns
        assert "nextjs-testing.md" in output.patterns
        assert (
            output.patterns["rails-testing.md"] != output.patterns["nextjs-testing.md"]
        )

    def test_each_stack_reads_its_own(self):
        output = render_all(compose_stacks(["rails", "nextjs"]))

        assert "rails-security.md" in output.agents["backend-reviewer.md"]
        assert "nextjs-security.md" not in output.agents["backend-reviewer.md"]

    def test_single_stack_keeps_plain_names(self):
        output = render_all(compose_stacks(["rails"]))
        assert "testing.md" in output.patterns
        assert "rails-testing.md" not in output.patterns

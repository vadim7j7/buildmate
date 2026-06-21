"""Tests for the project-root scaffold mechanism and standard-app profiles."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import compose_stacks, load_profile, load_stack
from lib.installer import install
from lib.renderer import render_all

STANDARD_LOCALES = "en,es,fr,de,it,pt-BR,nl,pl,tr,vi,id,ja,ko,ru,zh,tl,th,ms"


class TestScaffoldConfig:
    """Stack-level scaffold parsing and inheritance."""

    def test_react_native_scaffold_enabled(self):
        stack = load_stack("react-native")
        assert stack.scaffold_enabled is True
        assert stack.scaffold_source == "scaffold"

    def test_nextjs_scaffold_enabled_through_inheritance(self):
        # nextjs extends javascript; scaffold is declared on nextjs itself.
        stack = load_stack("nextjs")
        assert stack.scaffold_enabled is True

    def test_stack_without_scaffold_defaults_false(self):
        stack = load_stack("rails")
        assert stack.scaffold_enabled is False


class TestCollectScaffold:
    """render_all should collect rendered/verbatim scaffold files."""

    def test_single_stack_scaffold_at_root(self):
        composed = compose_stacks(["react-native"])
        output = render_all(composed)
        # Single stack -> working_dir "." -> no prefix.
        assert "eas.json" in output.scaffold
        assert "fastlane/Fastfile" in output.scaffold
        assert "src/i18n/index.ts" in output.scaffold
        # .j2 suffix is stripped.
        assert not any(p.endswith(".j2") for p in output.scaffold)

    def test_multi_stack_scaffold_prefixed_by_working_dir(self):
        composed = compose_stacks(["react-native", "nextjs"])
        output = render_all(composed)
        assert "mobile/eas.json" in output.scaffold
        assert "mobile/Makefile" in output.scaffold
        assert "web/src/i18n/config.ts" in output.scaffold
        assert "web/next.config.ts" in output.scaffold

    def test_locale_set_rendered_into_scaffold(self):
        composed = compose_stacks(["react-native", "nextjs"])
        output = render_all(composed)
        mobile_i18n = output.scaffold["mobile/src/i18n/index.ts"]
        web_i18n = output.scaffold["web/src/i18n/config.ts"]
        assert isinstance(mobile_i18n, str)
        assert isinstance(web_i18n, str)
        # Every standard locale appears in both rendered configs.
        for loc in STANDARD_LOCALES.split(","):
            assert f'"{loc}"' in mobile_i18n
            assert f'"{loc}"' in web_i18n

    def test_verbatim_file_kept_as_path(self):
        composed = compose_stacks(["react-native"])
        output = render_all(composed)
        render_script = output.scaffold["fastlane/screenshots/render_captions.sh"]
        # Non-.j2 files are passed through as source Paths.
        assert isinstance(render_script, Path)
        assert render_script.exists()


class TestLanguagesOption:
    """The languages option drives the locale variables on both stacks."""

    def test_minimal_overrides_locales(self):
        composed = compose_stacks(
            ["react-native"], options={"react-native": {"languages": "minimal"}}
        )
        assert composed.variables["locales"] == "en,es"
        assert composed.variables["locale_count"] == 2

    def test_standard_default(self):
        composed = compose_stacks(["nextjs"])
        assert composed.variables["locales"] == STANDARD_LOCALES
        assert composed.variables["default_locale"] == "en"


class TestScaffoldInstall:
    """Installer writes scaffold under the project root, not .claude/."""

    def test_scaffold_written_to_project_root(self):
        composed = compose_stacks(["react-native", "nextjs"])
        output = render_all(composed)
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            result = install(output, target, ["react-native", "nextjs"])
            assert (target / "mobile" / "eas.json").exists()
            assert (target / "mobile" / "fastlane" / "Fastfile").exists()
            assert (target / "web" / "src" / "i18n" / "config.ts").exists()
            # Not under .claude/
            assert not (target / ".claude" / "mobile").exists()
            assert result.scaffold_count > 0

    def test_shell_scripts_executable(self):
        composed = compose_stacks(["react-native"])
        output = render_all(composed)
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["react-native"])
            script = target / "fastlane" / "capture-screenshots.sh"
            assert script.exists()
            import os

            assert os.access(script, os.X_OK)

    def test_existing_file_not_clobbered_without_force(self):
        composed = compose_stacks(["react-native"])
        output = render_all(composed)
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            (target / "eas.json").write_text('{"existing": true}')
            result = install(output, target, ["react-native"])
            assert (target / "eas.json").read_text() == '{"existing": true}'
            assert "eas.json" in result.scaffold_skipped

    def test_scaffold_files_in_lockfile(self):
        composed = compose_stacks(["react-native", "nextjs"])
        output = render_all(composed)
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            result = install(output, target, ["react-native", "nextjs"])
            assert result.lock is not None
            assert "mobile/eas.json" in result.lock.file_checksums

    def test_dry_run_writes_nothing(self):
        composed = compose_stacks(["react-native"])
        output = render_all(composed)
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["react-native"], dry_run=True)
            assert not (target / "eas.json").exists()


class TestStandardAppProfiles:
    """The two standard-app profiles compose and pin the shared locale set."""

    def test_standard_app_profile(self):
        profile = load_profile("standard-app")
        assert profile.stacks == ["react-native", "nextjs"]
        composed = compose_stacks(profile.stacks, profile=profile)
        assert composed.variables["locales"] == STANDARD_LOCALES
        assert composed.variables["project_type"] == "standard-app"
        # The locale set surfaces in CLAUDE.md as the canonical reference.
        output = render_all(composed)
        assert "## Localization" in output.claude_md
        assert STANDARD_LOCALES in output.claude_md

    def test_standard_app_api_profile(self):
        profile = load_profile("standard-app-api")
        assert profile.stacks == ["react-native", "nextjs", "fastapi"]
        # Composing the trio must pass compatibility (nextjs<->react-native fix).
        composed = compose_stacks(profile.stacks, profile=profile)
        assert composed.variables["locales"] == STANDARD_LOCALES
        assert {s.name for s in composed.stacks} == {
            "react-native",
            "nextjs",
            "fastapi",
        }

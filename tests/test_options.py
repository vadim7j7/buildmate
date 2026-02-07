"""Tests for stack options and profiles."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import (
    compose_stacks,
    get_stack_options,
    list_available_profiles,
    load_profile,
)
from lib.renderer import render_all


class TestStackOptions:
    """Tests for stack options configuration."""

    def test_nextjs_has_ui_option(self):
        """Nextjs stack should have ui option."""
        options = get_stack_options("nextjs")
        assert "ui" in options
        assert options["ui"].default == "mantine"
        assert "mantine" in options["ui"].choices
        assert "tailwind" in options["ui"].choices
        assert "shadcn" in options["ui"].choices
        assert "chakra" in options["ui"].choices
        assert "mui" in options["ui"].choices
        assert "antd" in options["ui"].choices

    def test_nextjs_has_state_option(self):
        """Nextjs stack should have state option."""
        options = get_stack_options("nextjs")
        assert "state" in options
        assert options["state"].default == "zustand"
        assert "zustand" in options["state"].choices
        assert "redux" in options["state"].choices
        assert "mobx" in options["state"].choices
        assert "jotai" in options["state"].choices
        assert "context" in options["state"].choices
        assert "none" in options["state"].choices

    def test_rails_has_jobs_option(self):
        """Rails stack should have jobs option."""
        options = get_stack_options("rails")
        assert "jobs" in options
        assert options["jobs"].default == "sidekiq"
        assert "sidekiq" in options["jobs"].choices
        assert "good_job" in options["jobs"].choices
        assert "solid_queue" in options["jobs"].choices
        assert "active_job" in options["jobs"].choices

    def test_rails_has_db_option(self):
        """Rails stack should have db option."""
        options = get_stack_options("rails")
        assert "db" in options
        assert options["db"].default == "postgresql"
        assert "postgresql" in options["db"].choices
        assert "mysql" in options["db"].choices
        assert "sqlite" in options["db"].choices
        assert "mongodb" in options["db"].choices

    def test_react_native_has_state_option(self):
        """React-native stack should have state option."""
        options = get_stack_options("react-native")
        assert "state" in options
        assert options["state"].default == "zustand"
        assert "zustand" in options["state"].choices
        assert "mobx" in options["state"].choices
        assert "redux" in options["state"].choices
        assert "jotai" in options["state"].choices
        assert "none" in options["state"].choices

    def test_fastapi_has_db_option(self):
        """Fastapi stack should have db option."""
        options = get_stack_options("fastapi")
        assert "db" in options
        assert options["db"].default == "postgresql"
        assert "postgresql" in options["db"].choices
        assert "mysql" in options["db"].choices
        assert "sqlite" in options["db"].choices
        assert "mongodb" in options["db"].choices


class TestOptionsApplyPatterns:
    """Tests that options correctly apply patterns and styles."""

    def test_nextjs_tailwind_includes_tailwind_style(self):
        """Nextjs with tailwind option should include tailwind style."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"ui": "tailwind"}})
        output = render_all(composed)

        # Should have tailwind.md style
        assert "tailwind.md" in output.styles
        # Should NOT have mantine.md (default)
        assert "mantine.md" not in output.styles

    def test_nextjs_chakra_includes_chakra_style(self):
        """Nextjs with chakra option should include chakra style."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"ui": "chakra"}})
        output = render_all(composed)

        assert "chakra.md" in output.styles

    def test_nextjs_mui_includes_mui_style(self):
        """Nextjs with mui option should include mui style."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"ui": "mui"}})
        output = render_all(composed)

        assert "mui.md" in output.styles

    def test_nextjs_antd_includes_antd_style(self):
        """Nextjs with antd option should include antd style."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"ui": "antd"}})
        output = render_all(composed)

        assert "antd.md" in output.styles

    def test_nextjs_redux_includes_redux_pattern(self):
        """Nextjs with redux option should include redux pattern."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"state": "redux"}})
        output = render_all(composed)

        assert "redux.md" in output.patterns

    def test_nextjs_mobx_includes_mobx_pattern(self):
        """Nextjs with mobx option should include mobx pattern."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"state": "mobx"}})
        output = render_all(composed)

        assert "mobx.md" in output.patterns

    def test_nextjs_jotai_includes_jotai_pattern(self):
        """Nextjs with jotai option should include jotai pattern."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"state": "jotai"}})
        output = render_all(composed)

        assert "jotai.md" in output.patterns

    def test_rails_mongodb_includes_mongoid_pattern(self):
        """Rails with mongodb option should include mongoid pattern."""
        composed = compose_stacks(["rails"], options={"rails": {"db": "mongodb"}})
        output = render_all(composed)

        assert "mongoid.md" in output.patterns

    def test_rails_sidekiq_includes_sidekiq_pattern(self):
        """Rails with sidekiq option should include sidekiq pattern."""
        composed = compose_stacks(["rails"], options={"rails": {"jobs": "sidekiq"}})
        output = render_all(composed)

        assert "sidekiq.md" in output.patterns

    def test_rails_good_job_includes_good_job_pattern(self):
        """Rails with good_job option should include good_job pattern."""
        composed = compose_stacks(["rails"], options={"rails": {"jobs": "good_job"}})
        output = render_all(composed)

        assert "good_job.md" in output.patterns

    def test_react_native_redux_includes_redux_pattern(self):
        """React-native with redux option should include redux pattern."""
        composed = compose_stacks(
            ["react-native"], options={"react-native": {"state": "redux"}}
        )
        output = render_all(composed)

        assert "redux.md" in output.patterns

    def test_react_native_mobx_includes_mobx_pattern(self):
        """React-native with mobx option should include mobx pattern."""
        composed = compose_stacks(
            ["react-native"], options={"react-native": {"state": "mobx"}}
        )
        output = render_all(composed)

        assert "mobx.md" in output.patterns

    def test_react_native_jotai_includes_jotai_pattern(self):
        """React-native with jotai option should include jotai pattern."""
        composed = compose_stacks(
            ["react-native"], options={"react-native": {"state": "jotai"}}
        )
        output = render_all(composed)

        assert "jotai.md" in output.patterns

    def test_fastapi_mongodb_includes_mongodb_pattern(self):
        """Fastapi with mongodb option should include mongodb pattern."""
        composed = compose_stacks(["fastapi"], options={"fastapi": {"db": "mongodb"}})
        output = render_all(composed)

        assert "mongodb.md" in output.patterns


class TestOptionsApplyVariables:
    """Tests that options correctly apply variables."""

    def test_nextjs_tailwind_sets_ui_library_variable(self):
        """Nextjs with tailwind should set ui_library variable."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"ui": "tailwind"}})

        assert composed.variables.get("ui_library") == "Tailwind CSS"

    def test_nextjs_redux_sets_state_library_variable(self):
        """Nextjs with redux should set state_library variable."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"state": "redux"}})

        assert composed.variables.get("state_library") == "Redux Toolkit"

    def test_rails_mongodb_sets_orm_variable(self):
        """Rails with mongodb should set orm variable to Mongoid."""
        composed = compose_stacks(["rails"], options={"rails": {"db": "mongodb"}})

        assert composed.variables.get("orm") == "Mongoid"


class TestProfiles:
    """Tests for profile loading and application."""

    def test_list_profiles(self):
        """Should list available profiles."""
        profiles = list_available_profiles()

        assert "landing" in profiles
        assert "saas" in profiles
        assert "api-only" in profiles
        assert "mobile-backend" in profiles

    def test_load_landing_profile(self):
        """Should load landing profile correctly."""
        profile = load_profile("landing")

        assert profile.name == "landing"
        assert profile.stacks == ["nextjs"]
        assert profile.options["nextjs"]["ui"] == "tailwind"
        assert profile.options["nextjs"]["state"] == "none"

    def test_load_saas_profile(self):
        """Should load saas profile correctly."""
        profile = load_profile("saas")

        assert profile.name == "saas"
        assert "rails" in profile.stacks
        assert "nextjs" in profile.stacks
        assert profile.options["rails"]["jobs"] == "sidekiq"
        assert profile.options["rails"]["db"] == "postgresql"
        assert profile.options["nextjs"]["ui"] == "mantine"
        assert profile.options["nextjs"]["state"] == "zustand"

    def test_load_api_only_profile(self):
        """Should load api-only profile correctly."""
        profile = load_profile("api-only")

        assert profile.name == "api-only"
        assert profile.stacks == ["rails"]
        assert profile.options["rails"]["jobs"] == "sidekiq"
        assert profile.options["rails"]["db"] == "postgresql"

    def test_load_mobile_backend_profile(self):
        """Should load mobile-backend profile correctly."""
        profile = load_profile("mobile-backend")

        assert profile.name == "mobile-backend"
        assert "fastapi" in profile.stacks
        assert "react-native" in profile.stacks
        assert profile.options["fastapi"]["db"] == "postgresql"
        assert profile.options["react-native"]["state"] == "zustand"

    def test_profile_applies_options(self):
        """Profile options should be applied when composing."""
        profile = load_profile("landing")
        composed = compose_stacks(profile.stacks, profile=profile)
        output = render_all(composed)

        # Landing uses tailwind, not mantine
        assert "tailwind.md" in output.styles
        assert "mantine.md" not in output.styles

    def test_profile_saas_includes_both_stacks(self):
        """Saas profile should include both rails and nextjs agents."""
        profile = load_profile("saas")
        composed = compose_stacks(profile.stacks, profile=profile)
        output = render_all(composed)

        # Should have agents from both stacks
        assert "backend-developer.md" in output.agents
        assert "frontend-developer.md" in output.agents

    def test_profile_mobile_backend_uses_fastapi(self):
        """Mobile-backend profile should use fastapi, not rails."""
        profile = load_profile("mobile-backend")
        composed = compose_stacks(profile.stacks, profile=profile)
        output = render_all(composed)

        # Should have fastapi backend agents and mobile agents
        assert "backend-developer.md" in output.agents
        assert "mobile-developer.md" in output.agents

        # Backend patterns should be from fastapi (python)
        assert "backend-python.md" in output.styles


class TestOptionsOverrideProfile:
    """Tests that CLI options override profile defaults."""

    def test_cli_options_override_profile(self):
        """CLI options should override profile options."""
        profile = load_profile("saas")
        # Profile uses mantine, but we override with tailwind
        composed = compose_stacks(
            profile.stacks, profile=profile, options={"nextjs": {"ui": "tailwind"}}
        )
        output = render_all(composed)

        # Should have tailwind, not mantine
        assert "tailwind.md" in output.styles
        assert "mantine.md" not in output.styles


class TestDefaultOptions:
    """Tests that default options are applied when none specified."""

    def test_nextjs_defaults_to_mantine(self):
        """Nextjs without options should use mantine (default)."""
        composed = compose_stacks(["nextjs"])
        output = render_all(composed)

        assert "mantine.md" in output.styles

    def test_nextjs_defaults_to_zustand(self):
        """Nextjs without options should use zustand (default)."""
        composed = compose_stacks(["nextjs"])
        output = render_all(composed)

        assert "zustand.md" in output.patterns

    def test_rails_defaults_to_sidekiq(self):
        """Rails without options should use sidekiq (default)."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert "sidekiq.md" in output.patterns

    def test_react_native_defaults_to_zustand(self):
        """React-native without options should use zustand (default)."""
        composed = compose_stacks(["react-native"])
        output = render_all(composed)

        assert "zustand.md" in output.patterns


class TestRenderedContentContainsOptionValues:
    """Tests that rendered content reflects selected options."""

    def test_nextjs_tailwind_style_file_has_content(self):
        """Tailwind style file should have tailwind-specific content."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"ui": "tailwind"}})
        output = render_all(composed)

        # Should have tailwind style
        assert "tailwind.md" in output.styles
        content = output.styles["tailwind.md"].read_text()
        assert "Tailwind" in content or "tailwind" in content.lower()
        assert "class" in content.lower()  # Tailwind uses class-based styling

    def test_nextjs_redux_pattern_file_has_content(self):
        """Redux pattern file should have redux-specific content."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"state": "redux"}})
        output = render_all(composed)

        # Should have redux pattern
        assert "redux.md" in output.patterns
        content = output.patterns["redux.md"].read_text()
        assert "Redux" in content or "redux" in content.lower()
        assert "createSlice" in content or "reducer" in content.lower()

    def test_rails_mongodb_pattern_file_has_content(self):
        """Mongoid pattern file should have mongoid-specific content."""
        composed = compose_stacks(["rails"], options={"rails": {"db": "mongodb"}})
        output = render_all(composed)

        # Should have mongoid pattern
        assert "mongoid.md" in output.patterns
        content = output.patterns["mongoid.md"].read_text()
        assert "Mongoid" in content or "mongoid" in content.lower()
        assert "Document" in content  # Mongoid uses Document module

    def test_rails_good_job_pattern_file_has_content(self):
        """GoodJob pattern file should have good_job-specific content."""
        composed = compose_stacks(["rails"], options={"rails": {"jobs": "good_job"}})
        output = render_all(composed)

        # Should have good_job pattern
        assert "good_job.md" in output.patterns
        content = output.patterns["good_job.md"].read_text()
        assert "GoodJob" in content or "good_job" in content.lower()

    def test_pattern_file_content_is_not_empty(self):
        """Pattern files should have actual content."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"state": "redux"}})
        output = render_all(composed)

        # redux.md pattern should exist and source file should have content
        assert "redux.md" in output.patterns
        source_path = output.patterns["redux.md"]
        assert source_path.exists()
        content = source_path.read_text()
        assert len(content) > 100  # Should have substantial content
        assert "Redux" in content or "redux" in content.lower()

    def test_style_file_content_is_not_empty(self):
        """Style files should have actual content."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"ui": "chakra"}})
        output = render_all(composed)

        # chakra.md style should exist and source file should have content
        assert "chakra.md" in output.styles
        source_path = output.styles["chakra.md"]
        assert source_path.exists()
        content = source_path.read_text()
        assert len(content) > 100  # Should have substantial content
        assert "Chakra" in content or "chakra" in content.lower()

    def test_agent_references_correct_patterns(self):
        """Developer agent should reference the correct pattern files."""
        composed = compose_stacks(["nextjs"], options={"nextjs": {"state": "redux"}})
        output = render_all(composed)

        # Frontend developer should mention patterns
        dev_content = output.agents.get("frontend-developer.md", "")
        # Should reference patterns directory
        assert "patterns" in dev_content.lower()

    def test_multistack_has_both_stack_content(self):
        """Multi-stack composition should have content from both stacks."""
        composed = compose_stacks(["rails", "nextjs"])
        output = render_all(composed)

        # CLAUDE.md should mention both
        content = output.claude_md.lower()
        assert "rails" in content
        assert "next" in content or "react" in content

        # Should have agents from both
        assert "backend-developer.md" in output.agents
        assert "frontend-developer.md" in output.agents

        # Backend developer should mention Rails/Ruby
        backend_content = output.agents["backend-developer.md"].lower()
        assert "rails" in backend_content or "ruby" in backend_content

        # Frontend developer should mention React/Next
        frontend_content = output.agents["frontend-developer.md"].lower()
        assert "next" in frontend_content or "react" in frontend_content


class TestProfileRenderedContent:
    """Tests that profile-composed content is correct."""

    def test_landing_profile_has_tailwind_content(self):
        """Landing profile should render with tailwind content."""
        profile = load_profile("landing")
        composed = compose_stacks(profile.stacks, profile=profile)
        output = render_all(composed)

        # Should have tailwind style with actual content
        assert "tailwind.md" in output.styles
        source_path = output.styles["tailwind.md"]
        content = source_path.read_text()
        assert "Tailwind" in content

    def test_saas_profile_has_fullstack_content(self):
        """Saas profile should have both backend and frontend content."""
        profile = load_profile("saas")
        composed = compose_stacks(profile.stacks, profile=profile)
        output = render_all(composed)

        # Should have backend patterns (sidekiq is default for saas)
        assert "sidekiq.md" in output.patterns
        sidekiq_content = output.patterns["sidekiq.md"].read_text()
        assert "Sidekiq" in sidekiq_content

        # Should have frontend patterns (zustand is default for saas)
        assert "zustand.md" in output.patterns
        zustand_content = output.patterns["zustand.md"].read_text()
        assert "zustand" in zustand_content.lower()

    def test_mobile_backend_profile_has_python_content(self):
        """Mobile-backend profile should have FastAPI/Python content."""
        profile = load_profile("mobile-backend")
        composed = compose_stacks(profile.stacks, profile=profile)
        output = render_all(composed)

        # Backend developer should mention Python/FastAPI
        backend_content = output.agents["backend-developer.md"].lower()
        assert "python" in backend_content or "fastapi" in backend_content

        # Should have python style
        assert "backend-python.md" in output.styles

        # Mobile developer should mention React Native
        mobile_content = output.agents["mobile-developer.md"].lower()
        assert "react native" in mobile_content or "expo" in mobile_content


class TestPatternFilesExist:
    """Tests that all referenced pattern and style files exist."""

    def test_nextjs_ui_style_files_exist(self):
        """All nextjs UI style files should exist."""
        from lib.config import STACKS_DIR

        ui_styles = [
            "mantine.md",
            "tailwind.md",
            "shadcn.md",
            "chakra.md",
            "mui.md",
            "antd.md",
        ]
        for style in ui_styles:
            path = STACKS_DIR / "nextjs" / "styles" / style
            assert path.exists(), f"Missing style file: {path}"

    def test_nextjs_state_pattern_files_exist(self):
        """All nextjs state pattern files should exist."""
        from lib.config import STACKS_DIR

        patterns = ["zustand.md", "redux.md", "mobx.md", "jotai.md", "context.md"]
        for pattern in patterns:
            path = STACKS_DIR / "nextjs" / "patterns" / pattern
            assert path.exists(), f"Missing pattern file: {path}"

    def test_rails_job_pattern_files_exist(self):
        """All rails job pattern files should exist."""
        from lib.config import STACKS_DIR

        patterns = ["sidekiq.md", "good_job.md", "solid_queue.md"]
        for pattern in patterns:
            path = STACKS_DIR / "rails" / "patterns" / pattern
            assert path.exists(), f"Missing pattern file: {path}"

    def test_rails_mongodb_pattern_exists(self):
        """Rails mongoid pattern file should exist."""
        from lib.config import STACKS_DIR

        path = STACKS_DIR / "rails" / "patterns" / "mongoid.md"
        assert path.exists(), f"Missing pattern file: {path}"

    def test_react_native_state_pattern_files_exist(self):
        """All react-native state pattern files should exist."""
        from lib.config import STACKS_DIR

        patterns = ["zustand.md", "redux.md", "mobx.md", "jotai.md"]
        for pattern in patterns:
            path = STACKS_DIR / "react-native" / "patterns" / pattern
            assert path.exists(), f"Missing pattern file: {path}"

    def test_fastapi_mongodb_pattern_exists(self):
        """Fastapi mongodb pattern file should exist."""
        from lib.config import STACKS_DIR

        path = STACKS_DIR / "fastapi" / "patterns" / "mongodb.md"
        assert path.exists(), f"Missing pattern file: {path}"

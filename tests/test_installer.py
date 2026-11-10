"""Tests for installer module."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import compose_stacks
from lib.installer import InstallResult, install
from lib.renderer import render_all


class TestInstall:
    """Tests for install function."""

    def test_install_creates_claude_directory(self):
        """Install should create .claude directory."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            assert (target / ".claude").exists()
            assert (target / ".claude").is_dir()

    def test_install_creates_agents_directory(self):
        """Install should create agents directory with files."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            agents_dir = target / ".claude" / "agents"
            assert agents_dir.exists()
            assert (agents_dir / "orchestrator.md").exists()
            assert (agents_dir / "backend-developer.md").exists()

    def test_install_creates_skills_directory(self):
        """Install should create skills directory."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            skills_dir = target / ".claude" / "skills"
            assert skills_dir.exists()

    def test_install_creates_patterns_directory(self):
        """Install should create patterns directory."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            patterns_dir = target / ".claude" / "patterns"
            assert patterns_dir.exists()

    def test_install_creates_styles_directory(self):
        """Install should create styles directory."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            styles_dir = target / ".claude" / "styles"
            assert styles_dir.exists()

    def test_install_creates_context_directory(self):
        """Install should create context/features directory."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            context_dir = target / ".claude" / "context" / "features"
            assert context_dir.exists()

    def test_install_creates_claude_md(self):
        """Install should create CLAUDE.md file."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            claude_md = target / "CLAUDE.md"
            assert claude_md.exists()
            content = claude_md.read_text()
            assert len(content) > 0

    def test_install_creates_readme(self):
        """Install should create .claude/README.md file."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            readme = target / ".claude" / "README.md"
            assert readme.exists()

    def test_install_creates_settings_json(self):
        """Install should create settings.json file."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            settings = target / ".claude" / "settings.json"
            assert settings.exists()

    def test_install_force_overwrites(self):
        """Install with force should overwrite existing directory."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # First install
            install(output, target, ["rails"])

            # Create a marker file
            marker = target / ".claude" / "marker.txt"
            marker.write_text("test")

            # Second install with force
            install(output, target, ["rails"], force=True)

            # Marker should be gone
            assert not marker.exists()

    def test_install_without_force_fails_on_existing(self):
        """Install without force should fail if .claude exists."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Create existing .claude directory
            (target / ".claude").mkdir()

            # Should return result with errors
            result = install(output, target, ["rails"], force=False)
            assert len(result.errors) > 0
            assert ".claude/ already exists" in result.errors[0]

    def test_install_dry_run_creates_nothing(self):
        """Install with dry_run should not create any files."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"], dry_run=True)

            # Nothing should be created
            assert not (target / ".claude").exists()
            assert not (target / "CLAUDE.md").exists()

    def test_install_multi_stack(self):
        """Install multi-stack should include files from all stacks."""
        composed = compose_stacks(["rails", "nextjs"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails", "nextjs"])

            agents_dir = target / ".claude" / "agents"
            # Should have agents from both stacks
            assert (agents_dir / "backend-developer.md").exists()
            assert (agents_dir / "frontend-developer.md").exists()

            # Should have patterns from both
            patterns_dir = target / ".claude" / "patterns"
            files = list(patterns_dir.iterdir())
            assert len(files) >= 2

    def test_install_returns_result(self):
        """Install should return InstallResult with counts."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            result = install(output, target, ["rails"])

            assert isinstance(result, InstallResult)
            assert result.agents_count > 0
            assert result.target_path == target


class TestInstallMcpAndHooks:
    """Tests for .mcp.json, hook matchers and Buildmate-only skills."""

    def test_install_writes_mcp_json_not_settings(self):
        """MCP servers go to <target>/.mcp.json, not .claude/settings.json."""
        import json

        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            install(output, target, ["rails"])

            settings = json.loads((target / ".claude" / "settings.json").read_text())
            assert "mcpServers" not in settings
            assert "puppeteer" in settings["enabledMcpjsonServers"]

            mcp = json.loads((target / ".mcp.json").read_text())
            args = mcp["mcpServers"]["puppeteer"]["args"]
            assert "@modelcontextprotocol/server-puppeteer" in args

    def test_install_merges_existing_mcp_json(self):
        """Servers already in .mcp.json are kept."""
        import json

        composed = compose_stacks(["rails"])
        output = render_all(composed)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            (target / ".mcp.json").write_text(
                json.dumps({"mcpServers": {"mine": {"command": "my-server"}}})
            )
            install(output, target, ["rails"])

            servers = json.loads((target / ".mcp.json").read_text())["mcpServers"]
            assert servers["mine"] == {"command": "my-server"}
            assert "puppeteer" in servers

    def test_subagent_hook_matches_agent_tool(self):
        """The subagent hook fires for the Agent tool and has no unknown keys."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        post = output.settings["hooks"]["PostToolUse"]
        matchers = [m.get("matcher", "") for m in post]
        assert any("Agent" in m.split("|") for m in matchers)
        for event in output.settings["hooks"].values():
            for entry in event:
                for hook in entry["hooks"]:
                    assert "blocking" not in hook

    def test_new_stack_skill_not_installed(self):
        """new-stack is for working on Buildmate itself, not target projects."""
        composed = compose_stacks(["rails"])
        output = render_all(composed)

        assert "new-stack" not in output.skills


class TestInstallResult:
    """Tests for InstallResult dataclass."""

    def test_install_result_properties(self):
        """InstallResult should have expected properties."""
        result = InstallResult(
            target_path=Path("/tmp/test"),
            agents_count=5,
            skills_count=10,
            patterns_count=2,
        )

        assert result.target_path == Path("/tmp/test")
        assert result.agents_count == 5
        assert result.skills_count == 10
        assert result.patterns_count == 2

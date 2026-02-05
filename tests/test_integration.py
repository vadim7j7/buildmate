"""Integration tests for the full bootstrap pipeline."""

import pytest
from pathlib import Path
import tempfile
import subprocess
import os
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBootstrapCLI:
    """Integration tests for bootstrap.py CLI."""

    @pytest.fixture
    def bootstrap_script(self):
        """Path to bootstrap.py script."""
        return Path(__file__).parent.parent / "bootstrap.py"

    @pytest.fixture
    def python_exe(self):
        """Path to Python executable in venv."""
        venv_python = Path(__file__).parent.parent / ".venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)
        return sys.executable

    def test_list_stacks(self, bootstrap_script, python_exe):
        """--list should show available stacks."""
        result = subprocess.run(
            [python_exe, str(bootstrap_script), "--list"],
            capture_output=True,
            text=True,
            cwd=bootstrap_script.parent,
        )
        assert result.returncode == 0
        assert "rails" in result.stdout
        assert "nextjs" in result.stdout
        assert "react-native" in result.stdout
        assert "fastapi" in result.stdout

    def test_validate_rails(self, bootstrap_script, python_exe):
        """--validate rails should pass."""
        result = subprocess.run(
            [python_exe, str(bootstrap_script), "--validate", "rails"],
            capture_output=True,
            text=True,
            cwd=bootstrap_script.parent,
        )
        assert result.returncode == 0
        assert "valid" in result.stdout.lower()

    def test_validate_nextjs(self, bootstrap_script, python_exe):
        """--validate nextjs should pass."""
        result = subprocess.run(
            [python_exe, str(bootstrap_script), "--validate", "nextjs"],
            capture_output=True,
            text=True,
            cwd=bootstrap_script.parent,
        )
        assert result.returncode == 0

    def test_validate_react_native(self, bootstrap_script, python_exe):
        """--validate react-native should pass."""
        result = subprocess.run(
            [python_exe, str(bootstrap_script), "--validate", "react-native"],
            capture_output=True,
            text=True,
            cwd=bootstrap_script.parent,
        )
        assert result.returncode == 0

    def test_validate_fastapi(self, bootstrap_script, python_exe):
        """--validate fastapi should pass."""
        result = subprocess.run(
            [python_exe, str(bootstrap_script), "--validate", "fastapi"],
            capture_output=True,
            text=True,
            cwd=bootstrap_script.parent,
        )
        assert result.returncode == 0

    def test_validate_invalid_stack(self, bootstrap_script, python_exe):
        """--validate with invalid stack should fail."""
        result = subprocess.run(
            [python_exe, str(bootstrap_script), "--validate", "nonexistent"],
            capture_output=True,
            text=True,
            cwd=bootstrap_script.parent,
        )
        assert result.returncode != 0

    def test_bootstrap_rails(self, bootstrap_script, python_exe):
        """Bootstrap rails stack should succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [python_exe, str(bootstrap_script), "rails", tmpdir],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )
            assert result.returncode == 0
            assert Path(tmpdir, ".claude").exists()
            assert Path(tmpdir, ".claude", "agents", "orchestrator.md").exists()
            assert Path(tmpdir, ".claude", "agents", "backend-developer.md").exists()
            assert Path(tmpdir, "CLAUDE.md").exists()

    def test_bootstrap_nextjs(self, bootstrap_script, python_exe):
        """Bootstrap nextjs stack should succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [python_exe, str(bootstrap_script), "nextjs", tmpdir],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )
            assert result.returncode == 0
            assert Path(tmpdir, ".claude", "agents", "frontend-developer.md").exists()

    def test_bootstrap_react_native(self, bootstrap_script, python_exe):
        """Bootstrap react-native stack should succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [python_exe, str(bootstrap_script), "react-native", tmpdir],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )
            assert result.returncode == 0
            assert Path(tmpdir, ".claude", "agents", "mobile-developer.md").exists()

    def test_bootstrap_fastapi(self, bootstrap_script, python_exe):
        """Bootstrap fastapi stack should succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [python_exe, str(bootstrap_script), "fastapi", tmpdir],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )
            assert result.returncode == 0
            assert Path(tmpdir, ".claude", "agents", "backend-developer.md").exists()

    def test_bootstrap_multi_stack(self, bootstrap_script, python_exe):
        """Bootstrap multi-stack should succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [python_exe, str(bootstrap_script), "rails,nextjs", tmpdir],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )
            assert result.returncode == 0

            # Should have agents from both stacks
            assert Path(tmpdir, ".claude", "agents", "backend-developer.md").exists()
            assert Path(tmpdir, ".claude", "agents", "frontend-developer.md").exists()

            # Should have patterns from both
            patterns_dir = Path(tmpdir, ".claude", "patterns")
            pattern_files = list(patterns_dir.iterdir())
            assert len(pattern_files) >= 2

    def test_bootstrap_dry_run(self, bootstrap_script, python_exe):
        """Bootstrap with --dry-run should not create files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [python_exe, str(bootstrap_script), "rails", tmpdir, "--dry-run"],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )
            assert result.returncode == 0
            assert not Path(tmpdir, ".claude").exists()

    def test_bootstrap_force(self, bootstrap_script, python_exe):
        """Bootstrap with --force should overwrite existing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First bootstrap
            subprocess.run(
                [python_exe, str(bootstrap_script), "rails", tmpdir],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )

            # Second bootstrap with force
            result = subprocess.run(
                [python_exe, str(bootstrap_script), "rails", tmpdir, "--force"],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )
            assert result.returncode == 0

    def test_bootstrap_without_force_fails(self, bootstrap_script, python_exe):
        """Bootstrap without --force should fail if .claude exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing .claude
            Path(tmpdir, ".claude").mkdir()

            result = subprocess.run(
                [python_exe, str(bootstrap_script), "rails", tmpdir],
                capture_output=True,
                text=True,
                cwd=bootstrap_script.parent,
            )
            assert result.returncode != 0

    def test_bootstrap_missing_target(self, bootstrap_script, python_exe):
        """Bootstrap with missing target should fail."""
        result = subprocess.run(
            [python_exe, str(bootstrap_script), "rails", "/nonexistent/path"],
            capture_output=True,
            text=True,
            cwd=bootstrap_script.parent,
        )
        assert result.returncode != 0


class TestBootstrapOutput:
    """Tests for bootstrap output structure and content."""

    @pytest.fixture
    def bootstrapped_rails(self):
        """Create a bootstrapped rails project."""
        from lib.config import compose_stacks
        from lib.renderer import render_all
        from lib.installer import install

        composed = compose_stacks(["rails"])
        output = render_all(composed)

        tmpdir = tempfile.mkdtemp()
        target = Path(tmpdir)
        install(output, target, ["rails"])

        yield target

        # Cleanup
        shutil.rmtree(tmpdir)

    def test_output_has_all_base_agents(self, bootstrapped_rails):
        """Output should have all base agents."""
        agents_dir = bootstrapped_rails / ".claude" / "agents"
        assert (agents_dir / "orchestrator.md").exists()
        assert (agents_dir / "grind.md").exists()
        assert (agents_dir / "eval-agent.md").exists()
        assert (agents_dir / "security-auditor.md").exists()

    def test_output_has_core_skills(self, bootstrapped_rails):
        """Output should have core skills."""
        skills_dir = bootstrapped_rails / ".claude" / "skills"
        # Core skills from base
        assert (skills_dir / "delegate").exists() or (skills_dir / "test").exists()

    def test_output_agent_content_valid(self, bootstrapped_rails):
        """Agent files should have valid content."""
        orchestrator = bootstrapped_rails / ".claude" / "agents" / "orchestrator.md"
        content = orchestrator.read_text()

        # Should have frontmatter
        assert content.startswith("---")
        assert "name:" in content

        # Should have content after frontmatter
        lines = content.split("\n")
        assert len(lines) > 10

    def test_output_claude_md_content(self, bootstrapped_rails):
        """CLAUDE.md should have expected content."""
        claude_md = bootstrapped_rails / "CLAUDE.md"
        content = claude_md.read_text()

        # Should mention the stack
        assert "rails" in content.lower() or "Rails" in content

        # Should have sections
        assert "#" in content

    def test_output_readme_content(self, bootstrapped_rails):
        """README.md should have expected content."""
        readme = bootstrapped_rails / ".claude" / "README.md"
        content = readme.read_text()

        # Should have instructions
        assert "#" in content
        assert len(content) > 100

    def test_output_settings_valid_json(self, bootstrapped_rails):
        """settings.json should be valid JSON."""
        import json
        settings = bootstrapped_rails / ".claude" / "settings.json"
        content = settings.read_text()

        # Should be valid JSON
        data = json.loads(content)
        assert isinstance(data, dict)

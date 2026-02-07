"""
Tests for project extensibility features:
- Lock file operations
- --add-stack command
- --set-option command
- --upgrade command
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from lib.lockfile import (
    BootstrapLock,
    StackLockInfo,
    create_lock,
    load_lock,
    save_lock,
    get_lock_path,
    compute_file_checksum,
    compute_checksums,
    get_modified_files,
    merge_locks,
)
from lib.config import compose_stacks
from lib.renderer import render_all
from lib.installer import install


# =============================================================================
# Lock File Unit Tests
# =============================================================================

class TestStackLockInfo:
    """Tests for StackLockInfo dataclass."""

    def test_create_stack_lock_info(self):
        info = StackLockInfo(name="rails", options={"jobs": "sidekiq"})
        assert info.name == "rails"
        assert info.options == {"jobs": "sidekiq"}

    def test_to_dict(self):
        info = StackLockInfo(name="nextjs", options={"ui": "tailwind"})
        result = info.to_dict()
        assert result == {"name": "nextjs", "options": {"ui": "tailwind"}}

    def test_from_dict(self):
        data = {"name": "rails", "options": {"db": "postgresql"}}
        info = StackLockInfo.from_dict(data)
        assert info.name == "rails"
        assert info.options == {"db": "postgresql"}

    def test_from_dict_without_options(self):
        data = {"name": "rails"}
        info = StackLockInfo.from_dict(data)
        assert info.name == "rails"
        assert info.options == {}


class TestBootstrapLock:
    """Tests for BootstrapLock dataclass."""

    def test_create_lock(self):
        lock = BootstrapLock(
            version="2.0.0",
            installed_at="2024-01-15T10:30:00Z",
        )
        assert lock.version == "2.0.0"
        assert lock.installed_at == "2024-01-15T10:30:00Z"
        assert lock.stacks == {}
        assert lock.profile is None

    def test_add_stack(self):
        lock = BootstrapLock(version="2.0.0", installed_at="2024-01-15T10:30:00Z")
        lock.add_stack("rails", {"jobs": "sidekiq"})
        assert lock.has_stack("rails")
        assert lock.stacks["rails"].options == {"jobs": "sidekiq"}

    def test_has_stack(self):
        lock = BootstrapLock(version="2.0.0", installed_at="2024-01-15T10:30:00Z")
        lock.add_stack("rails")
        assert lock.has_stack("rails")
        assert not lock.has_stack("nextjs")

    def test_get_stack_names(self):
        lock = BootstrapLock(version="2.0.0", installed_at="2024-01-15T10:30:00Z")
        lock.add_stack("rails")
        lock.add_stack("nextjs")
        names = lock.get_stack_names()
        assert "rails" in names
        assert "nextjs" in names

    def test_get_options(self):
        lock = BootstrapLock(version="2.0.0", installed_at="2024-01-15T10:30:00Z")
        lock.add_stack("rails", {"jobs": "sidekiq", "db": "postgresql"})
        lock.add_stack("nextjs", {"ui": "tailwind"})
        options = lock.get_options()
        assert options["rails"] == {"jobs": "sidekiq", "db": "postgresql"}
        assert options["nextjs"] == {"ui": "tailwind"}

    def test_set_option(self):
        lock = BootstrapLock(version="2.0.0", installed_at="2024-01-15T10:30:00Z")
        lock.add_stack("nextjs", {"ui": "mantine"})
        lock.set_option("nextjs", "ui", "tailwind")
        assert lock.stacks["nextjs"].options["ui"] == "tailwind"

    def test_set_option_raises_for_missing_stack(self):
        lock = BootstrapLock(version="2.0.0", installed_at="2024-01-15T10:30:00Z")
        with pytest.raises(ValueError, match="Stack 'rails' not installed"):
            lock.set_option("rails", "jobs", "sidekiq")

    def test_to_dict(self):
        lock = BootstrapLock(
            version="2.0.0",
            installed_at="2024-01-15T10:30:00Z",
            profile="saas",
        )
        lock.add_stack("rails", {"jobs": "sidekiq"})
        result = lock.to_dict()
        assert result["version"] == "2.0.0"
        assert result["installed_at"] == "2024-01-15T10:30:00Z"
        assert result["profile"] == "saas"
        assert "rails" in result["stacks"]

    def test_from_dict(self):
        data = {
            "version": "2.0.0",
            "installed_at": "2024-01-15T10:30:00Z",
            "profile": "saas",
            "stacks": {
                "rails": {"name": "rails", "options": {"jobs": "sidekiq"}},
            },
            "file_checksums": {"CLAUDE.md": "abc123"},
        }
        lock = BootstrapLock.from_dict(data)
        assert lock.version == "2.0.0"
        assert lock.profile == "saas"
        assert lock.has_stack("rails")
        assert lock.file_checksums == {"CLAUDE.md": "abc123"}


class TestLockFilePersistence:
    """Tests for load_lock and save_lock."""

    def test_get_lock_path(self):
        path = get_lock_path(Path("/my/project"))
        assert path == Path("/my/project/.claude/bootstrap.lock")

    def test_save_and_load_lock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            lock = create_lock(
                stack_names=["rails", "nextjs"],
                selected_options={"rails": {"jobs": "sidekiq"}, "nextjs": {"ui": "tailwind"}},
                profile_name="saas",
            )
            save_lock(target, lock)

            # Verify file exists
            lock_path = get_lock_path(target)
            assert lock_path.exists()

            # Load and verify
            loaded = load_lock(target)
            assert loaded is not None
            assert loaded.profile == "saas"
            assert loaded.has_stack("rails")
            assert loaded.has_stack("nextjs")
            assert loaded.stacks["rails"].options == {"jobs": "sidekiq"}

    def test_load_lock_returns_none_if_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            result = load_lock(target)
            assert result is None

    def test_lock_file_is_valid_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            lock = create_lock(["rails"], {}, None)
            save_lock(target, lock)

            # Read and parse as YAML
            lock_path = get_lock_path(target)
            with open(lock_path) as f:
                data = yaml.safe_load(f)
            assert "version" in data
            assert "stacks" in data


class TestChecksums:
    """Tests for file checksum operations."""

    def test_compute_file_checksum(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("hello world")
            checksum = compute_file_checksum(test_file)
            assert len(checksum) == 32  # MD5 hex digest length
            assert checksum == "5eb63bbbe01eeed093cb22bb8f5acdc3"

    def test_compute_file_checksum_nonexistent(self):
        checksum = compute_file_checksum(Path("/nonexistent/file.txt"))
        assert checksum == ""

    def test_compute_checksums(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            (target / "file1.txt").write_text("content1")
            (target / "file2.txt").write_text("content2")

            checksums = compute_checksums(target, ["file1.txt", "file2.txt", "missing.txt"])
            assert "file1.txt" in checksums
            assert "file2.txt" in checksums
            assert "missing.txt" not in checksums

    def test_get_modified_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            (target / "file1.txt").write_text("original")
            (target / "file2.txt").write_text("original")

            # Create lock with original checksums
            lock = BootstrapLock(version="2.0.0", installed_at="2024-01-15T10:30:00Z")
            lock.file_checksums = compute_checksums(target, ["file1.txt", "file2.txt"])

            # Modify one file
            (target / "file1.txt").write_text("modified")

            # Check for modifications
            modified = get_modified_files(target, lock)
            assert "file1.txt" in modified
            assert "file2.txt" not in modified


class TestMergeLocks:
    """Tests for merge_locks function."""

    def test_merge_adds_new_stack(self):
        existing = BootstrapLock(version="1.0.0", installed_at="2024-01-15T10:30:00Z")
        existing.add_stack("rails", {"jobs": "sidekiq"})

        result = merge_locks(existing, ["nextjs"], {"nextjs": {"ui": "tailwind"}})

        assert result.has_stack("rails")
        assert result.has_stack("nextjs")
        assert result.stacks["nextjs"].options == {"ui": "tailwind"}

    def test_merge_updates_existing_options(self):
        existing = BootstrapLock(version="1.0.0", installed_at="2024-01-15T10:30:00Z")
        existing.add_stack("nextjs", {"ui": "mantine"})

        result = merge_locks(existing, [], {"nextjs": {"ui": "tailwind"}})

        assert result.stacks["nextjs"].options["ui"] == "tailwind"

    def test_merge_preserves_existing_stacks(self):
        existing = BootstrapLock(version="1.0.0", installed_at="2024-01-15T10:30:00Z")
        existing.add_stack("rails", {"jobs": "sidekiq"})

        result = merge_locks(existing, ["nextjs"], {})

        assert result.has_stack("rails")
        assert result.stacks["rails"].options == {"jobs": "sidekiq"}

    def test_merge_updates_version(self):
        from lib import __version__
        existing = BootstrapLock(version="1.0.0", installed_at="2024-01-15T10:30:00Z")
        existing.add_stack("rails")

        result = merge_locks(existing, [], {})

        assert result.version == __version__


# =============================================================================
# Integration Tests for CLI Commands
# =============================================================================

class TestInstallCreatesLockFile:
    """Tests that install creates a lock file."""

    def test_install_creates_lock_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            config = compose_stacks(["rails"])
            output = render_all(config)

            result = install(
                output=output,
                target_path=target,
                stacks=["rails"],
                selected_options={"rails": {"jobs": "sidekiq"}},
            )

            # Verify lock file was created
            lock = load_lock(target)
            assert lock is not None
            assert lock.has_stack("rails")
            assert lock.stacks["rails"].options == {"jobs": "sidekiq"}

    def test_install_lock_file_has_checksums(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            config = compose_stacks(["rails"])
            output = render_all(config)

            install(
                output=output,
                target_path=target,
                stacks=["rails"],
            )

            lock = load_lock(target)
            assert lock is not None
            assert len(lock.file_checksums) > 0
            assert "CLAUDE.md" in lock.file_checksums

    def test_install_with_profile_saves_profile_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            config = compose_stacks(["rails", "nextjs"])
            output = render_all(config)

            install(
                output=output,
                target_path=target,
                stacks=["rails", "nextjs"],
                profile_name="saas",
            )

            lock = load_lock(target)
            assert lock is not None
            assert lock.profile == "saas"


class TestAddStackCommand:
    """Tests for --add-stack CLI command."""

    def _run_bootstrap(self, *args):
        """Helper to run bootstrap.py."""
        result = subprocess.run(
            [sys.executable, "bootstrap.py", *args],
            capture_output=True,
            text=True,
        )
        return result

    def test_add_stack_to_existing_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # First, bootstrap with rails
            result = self._run_bootstrap("rails", str(target))
            assert result.returncode == 0

            # Verify initial state
            lock = load_lock(target)
            assert lock.has_stack("rails")
            assert not lock.has_stack("nextjs")

            # Add nextjs
            result = self._run_bootstrap("--add-stack", "nextjs", str(target))
            assert result.returncode == 0

            # Verify new state
            lock = load_lock(target)
            assert lock.has_stack("rails")
            assert lock.has_stack("nextjs")

    def test_add_stack_with_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with rails
            self._run_bootstrap("rails", str(target))

            # Add nextjs with options
            result = self._run_bootstrap(
                "--add-stack", "nextjs", str(target),
                "--ui=tailwind", "--state=redux"
            )
            assert result.returncode == 0

            lock = load_lock(target)
            assert lock.stacks["nextjs"].options.get("ui") == "tailwind"
            assert lock.stacks["nextjs"].options.get("state") == "redux"

    def test_add_stack_fails_if_already_installed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with rails
            self._run_bootstrap("rails", str(target))

            # Try to add rails again
            result = self._run_bootstrap("--add-stack", "rails", str(target))
            assert result.returncode == 1
            assert "already installed" in result.stdout

    def test_add_stack_fails_without_lock_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Try to add stack without initial bootstrap
            result = self._run_bootstrap("--add-stack", "nextjs", str(target))
            assert result.returncode == 1
            assert "No bootstrap installation found" in result.stdout

    def test_add_stack_preserves_existing_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with rails and specific options
            self._run_bootstrap("rails", str(target), "--jobs=good_job")

            # Add nextjs
            self._run_bootstrap("--add-stack", "nextjs", str(target))

            # Verify rails options preserved
            lock = load_lock(target)
            assert lock.stacks["rails"].options.get("jobs") == "good_job"


class TestSetOptionCommand:
    """Tests for --set-option CLI command."""

    def _run_bootstrap(self, *args):
        """Helper to run bootstrap.py."""
        result = subprocess.run(
            [sys.executable, "bootstrap.py", *args],
            capture_output=True,
            text=True,
        )
        return result

    def test_set_option_changes_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with nextjs and default ui (mantine)
            self._run_bootstrap("nextjs", str(target))

            lock = load_lock(target)
            # Default is mantine
            assert lock.stacks["nextjs"].options.get("ui") == "mantine"

            # Change to tailwind
            result = self._run_bootstrap("--set-option", "nextjs.ui=tailwind", str(target))
            assert result.returncode == 0

            lock = load_lock(target)
            assert lock.stacks["nextjs"].options.get("ui") == "tailwind"

    def test_set_option_updates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with nextjs
            self._run_bootstrap("nextjs", str(target), "--ui=mantine")

            # Change to tailwind
            self._run_bootstrap("--set-option", "nextjs.ui=tailwind", str(target))

            # Verify tailwind style file exists
            styles_dir = target / ".claude" / "styles"
            style_files = list(styles_dir.glob("*.md"))
            style_names = [f.name for f in style_files]
            assert "tailwind.md" in style_names

    def test_set_option_fails_for_invalid_stack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with rails
            self._run_bootstrap("rails", str(target))

            # Try to set option for nextjs (not installed)
            result = self._run_bootstrap("--set-option", "nextjs.ui=tailwind", str(target))
            assert result.returncode == 1
            assert "not installed" in result.stdout

    def test_set_option_fails_for_invalid_option(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with nextjs
            self._run_bootstrap("nextjs", str(target))

            # Try to set invalid option
            result = self._run_bootstrap("--set-option", "nextjs.invalid=value", str(target))
            assert result.returncode == 1
            assert "not found" in result.stdout

    def test_set_option_fails_for_invalid_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with nextjs
            self._run_bootstrap("nextjs", str(target))

            # Try to set invalid value
            result = self._run_bootstrap("--set-option", "nextjs.ui=invalid", str(target))
            assert result.returncode == 1
            assert "Invalid value" in result.stdout


class TestUpgradeCommand:
    """Tests for --upgrade CLI command."""

    def _run_bootstrap(self, *args):
        """Helper to run bootstrap.py."""
        result = subprocess.run(
            [sys.executable, "bootstrap.py", *args],
            capture_output=True,
            text=True,
        )
        return result

    def test_upgrade_preserves_stacks_and_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with rails and specific options
            self._run_bootstrap("rails", str(target), "--jobs=good_job", "--db=postgresql")

            original_lock = load_lock(target)

            # Upgrade
            result = self._run_bootstrap("--upgrade", str(target))
            assert result.returncode == 0

            # Verify options preserved
            lock = load_lock(target)
            assert lock.has_stack("rails")
            assert lock.stacks["rails"].options.get("jobs") == "good_job"
            assert lock.stacks["rails"].options.get("db") == "postgresql"

    def test_upgrade_updates_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap
            self._run_bootstrap("rails", str(target))

            # Manually change version in lock file to simulate old version
            lock = load_lock(target)
            lock.version = "1.0.0"
            save_lock(target, lock)

            # Upgrade
            result = self._run_bootstrap("--upgrade", str(target))
            assert result.returncode == 0

            # Verify version updated
            lock = load_lock(target)
            from lib import __version__
            assert lock.version == __version__

    def test_upgrade_fails_without_lock_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Try to upgrade without initial bootstrap
            result = self._run_bootstrap("--upgrade", str(target))
            assert result.returncode == 1
            assert "No bootstrap installation found" in result.stdout

    def test_upgrade_preserves_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with profile
            self._run_bootstrap("--profile", "saas", str(target))

            lock = load_lock(target)
            assert lock.profile == "saas"

            # Upgrade
            self._run_bootstrap("--upgrade", str(target))

            # Verify profile preserved
            lock = load_lock(target)
            assert lock.profile == "saas"

    def test_upgrade_detects_modified_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap
            self._run_bootstrap("rails", str(target))

            # Modify a file
            claude_md = target / "CLAUDE.md"
            claude_md.write_text(claude_md.read_text() + "\n# Custom section")

            # Upgrade (should show warning about modified files)
            result = self._run_bootstrap("--upgrade", str(target))
            assert result.returncode == 0
            assert "modified" in result.stdout.lower()


class TestDryRunExtensibility:
    """Tests for --dry-run with extensibility commands."""

    def _run_bootstrap(self, *args):
        """Helper to run bootstrap.py."""
        result = subprocess.run(
            [sys.executable, "bootstrap.py", *args],
            capture_output=True,
            text=True,
        )
        return result

    def test_add_stack_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with rails
            self._run_bootstrap("rails", str(target))

            original_lock = load_lock(target)

            # Dry run add nextjs
            result = self._run_bootstrap("--add-stack", "nextjs", str(target), "--dry-run")
            assert result.returncode == 0
            assert "DRY RUN" in result.stdout

            # Verify nothing changed
            lock = load_lock(target)
            assert not lock.has_stack("nextjs")

    def test_set_option_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with nextjs
            self._run_bootstrap("nextjs", str(target), "--ui=mantine")

            # Dry run set option
            result = self._run_bootstrap("--set-option", "nextjs.ui=tailwind", str(target), "--dry-run")
            assert result.returncode == 0
            assert "DRY RUN" in result.stdout

            # Verify nothing changed
            lock = load_lock(target)
            assert lock.stacks["nextjs"].options.get("ui") == "mantine"

    def test_upgrade_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap
            self._run_bootstrap("rails", str(target))

            # Manually change version
            lock = load_lock(target)
            lock.version = "1.0.0"
            save_lock(target, lock)

            # Dry run upgrade
            result = self._run_bootstrap("--upgrade", str(target), "--dry-run")
            assert result.returncode == 0
            assert "DRY RUN" in result.stdout

            # Verify version unchanged
            lock = load_lock(target)
            assert lock.version == "1.0.0"


class TestMultiStackExtensibility:
    """Tests for extensibility with multiple stacks."""

    def _run_bootstrap(self, *args):
        """Helper to run bootstrap.py."""
        result = subprocess.run(
            [sys.executable, "bootstrap.py", *args],
            capture_output=True,
            text=True,
        )
        return result

    def test_add_third_stack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with fastapi (compatible with react-native)
            self._run_bootstrap("fastapi", str(target))

            lock = load_lock(target)
            assert lock.has_stack("fastapi")

            # Add react-native (compatible with fastapi)
            result = self._run_bootstrap("--add-stack", "react-native", str(target))
            assert result.returncode == 0

            lock = load_lock(target)
            assert lock.has_stack("fastapi")
            assert lock.has_stack("react-native")

    def test_set_option_in_multistack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Bootstrap with rails + nextjs
            self._run_bootstrap("rails+nextjs", str(target), "--ui=mantine", "--jobs=sidekiq")

            # Change nextjs ui
            self._run_bootstrap("--set-option", "nextjs.ui=tailwind", str(target))

            # Change rails jobs
            self._run_bootstrap("--set-option", "rails.jobs=good_job", str(target))

            lock = load_lock(target)
            assert lock.stacks["nextjs"].options.get("ui") == "tailwind"
            assert lock.stacks["rails"].options.get("jobs") == "good_job"

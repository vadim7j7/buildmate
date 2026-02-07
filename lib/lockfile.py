"""
Lock file management for tracking installed bootstrap configuration.

The lock file (.claude/bootstrap.lock) tracks:
- Version of bootstrap used
- Installation timestamp
- Stacks installed with their options
- File checksums for detecting user modifications
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from . import __version__


@dataclass
class StackLockInfo:
    """Information about an installed stack."""

    name: str
    options: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "options": self.options,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StackLockInfo":
        return cls(
            name=data["name"],
            options=data.get("options", {}),
        )


@dataclass
class BootstrapLock:
    """Lock file data structure."""

    version: str
    installed_at: str
    stacks: dict[str, StackLockInfo] = field(default_factory=dict)
    profile: str | None = None
    file_checksums: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "installed_at": self.installed_at,
            "profile": self.profile,
            "stacks": {name: info.to_dict() for name, info in self.stacks.items()},
            "file_checksums": self.file_checksums,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BootstrapLock":
        stacks = {}
        for name, info in data.get("stacks", {}).items():
            stacks[name] = StackLockInfo.from_dict(info)

        return cls(
            version=data.get("version", "unknown"),
            installed_at=data.get("installed_at", ""),
            profile=data.get("profile"),
            stacks=stacks,
            file_checksums=data.get("file_checksums", {}),
        )

    def get_stack_names(self) -> list[str]:
        """Get list of installed stack names."""
        return list(self.stacks.keys())

    def get_options(self) -> dict[str, dict[str, str]]:
        """Get all options as {stack_name: {option: value}}."""
        return {name: info.options for name, info in self.stacks.items()}

    def add_stack(self, name: str, options: dict[str, str] | None = None) -> None:
        """Add a stack to the lock."""
        self.stacks[name] = StackLockInfo(name=name, options=options or {})

    def set_option(self, stack_name: str, option: str, value: str) -> None:
        """Set an option for a stack."""
        if stack_name not in self.stacks:
            raise ValueError(f"Stack '{stack_name}' not installed")
        self.stacks[stack_name].options[option] = value

    def has_stack(self, name: str) -> bool:
        """Check if a stack is installed."""
        return name in self.stacks


def get_lock_path(target_path: Path) -> Path:
    """Get the path to the lock file."""
    return target_path / ".claude" / "bootstrap.lock"


def load_lock(target_path: Path) -> BootstrapLock | None:
    """
    Load the lock file from a target directory.

    Returns None if no lock file exists.
    """
    lock_path = get_lock_path(target_path)

    if not lock_path.exists():
        return None

    try:
        content = lock_path.read_text()
        data = yaml.safe_load(content)
        return BootstrapLock.from_dict(data)
    except Exception as e:
        print(f"Warning: Failed to load lock file: {e}")
        return None


def save_lock(target_path: Path, lock: BootstrapLock) -> None:
    """Save the lock file to a target directory."""
    lock_path = get_lock_path(target_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    content = yaml.dump(lock.to_dict(), default_flow_style=False, sort_keys=False)
    lock_path.write_text(content)


def create_lock(
    stack_names: list[str],
    selected_options: dict[str, dict[str, str]],
    profile_name: str | None = None,
) -> BootstrapLock:
    """
    Create a new lock from composition results.

    Args:
        stack_names: List of stack names
        selected_options: Options per stack {stack_name: {option: value}}
        profile_name: Optional profile name used

    Returns:
        New BootstrapLock instance
    """
    lock = BootstrapLock(
        version=__version__,
        installed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        profile=profile_name,
    )

    for name in stack_names:
        options = selected_options.get(name, {})
        lock.add_stack(name, options)

    return lock


def compute_file_checksum(file_path: Path) -> str:
    """Compute MD5 checksum of a file."""
    if not file_path.exists():
        return ""

    content = file_path.read_bytes()
    return hashlib.md5(content).hexdigest()


def compute_checksums(target_path: Path, files: list[str]) -> dict[str, str]:
    """
    Compute checksums for a list of files relative to target path.

    Args:
        target_path: Base directory
        files: List of relative file paths

    Returns:
        Dict of {relative_path: checksum}
    """
    checksums = {}
    for rel_path in files:
        full_path = target_path / rel_path
        if full_path.exists():
            checksums[rel_path] = compute_file_checksum(full_path)
    return checksums


def get_modified_files(target_path: Path, lock: BootstrapLock) -> list[str]:
    """
    Get list of files that have been modified since installation.

    Args:
        target_path: Base directory
        lock: Lock file with original checksums

    Returns:
        List of relative paths that have been modified
    """
    modified = []

    for rel_path, original_checksum in lock.file_checksums.items():
        full_path = target_path / rel_path
        if full_path.exists():
            current_checksum = compute_file_checksum(full_path)
            if current_checksum != original_checksum:
                modified.append(rel_path)
        # If file was deleted, we don't consider it modified

    return modified


def merge_locks(
    existing: BootstrapLock,
    new_stacks: list[str],
    new_options: dict[str, dict[str, str]],
) -> BootstrapLock:
    """
    Merge new stacks/options into existing lock.

    Args:
        existing: Existing lock file
        new_stacks: New stacks to add
        new_options: New/updated options

    Returns:
        Updated lock (mutates existing)
    """
    # Add new stacks
    for stack_name in new_stacks:
        if not existing.has_stack(stack_name):
            options = new_options.get(stack_name, {})
            existing.add_stack(stack_name, options)

    # Update options for existing stacks
    for stack_name, options in new_options.items():
        if existing.has_stack(stack_name):
            for opt_name, opt_value in options.items():
                existing.set_option(stack_name, opt_name, opt_value)

    # Update metadata
    existing.version = __version__
    existing.installed_at = (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    return existing

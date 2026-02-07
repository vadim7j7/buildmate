"""
Install rendered output to target directory.
"""

import json
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path

from .lockfile import (
    BootstrapLock,
    compute_checksums,
    create_lock,
    save_lock,
)
from .renderer import RenderedOutput


@dataclass
class InstallResult:
    """Results from installation."""

    target_path: Path
    agents_count: int = 0
    skills_count: int = 0
    hooks_count: int = 0
    patterns_count: int = 0
    styles_count: int = 0
    files_written: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False
    lock: BootstrapLock | None = None
    modified_files: list[str] = field(default_factory=list)


def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def make_executable(path: Path) -> None:
    """Make a file executable."""
    current = path.stat().st_mode
    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def copy_directory(src: Path, dst: Path) -> int:
    """
    Copy a directory recursively.

    Args:
        src: Source directory
        dst: Destination directory

    Returns:
        Number of files copied
    """
    if not src.exists():
        return 0

    count = 0
    ensure_directory(dst)

    for item in src.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(src)
            dst_file = dst / rel_path
            ensure_directory(dst_file.parent)
            shutil.copy2(item, dst_file)
            count += 1

    return count


def update_gitignore(target_path: Path) -> None:
    """
    Add agent-related directories to .gitignore.

    Args:
        target_path: Project root directory
    """
    gitignore_path = target_path / ".gitignore"
    entries = [
        ".agent-status/",
        ".agent-pipeline/",
        ".agent-eval-results/",
        ".claude/settings.local.json",
        ".claude/context/agent-activity.log",
        ".claude/context/session-summary.md",
    ]

    existing_lines = set()
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            existing_lines = set(line.strip() for line in f)

    new_entries = [e for e in entries if e not in existing_lines]

    if new_entries:
        with open(gitignore_path, "a") as f:
            if existing_lines and not gitignore_path.read_text().endswith("\n"):
                f.write("\n")
            f.write("\n# Claude Code agent directories\n")
            for entry in new_entries:
                f.write(f"{entry}\n")


def create_settings_local_template(claude_dir: Path) -> None:
    """
    Create settings.local.json template if it doesn't exist.

    Args:
        claude_dir: .claude directory path
    """
    settings_local = claude_dir / "settings.local.json"
    if not settings_local.exists():
        template = {"permissions": {"allow": [], "deny": []}}
        with open(settings_local, "w") as f:
            json.dump(template, f, indent=2)
            f.write("\n")


def install(
    output: RenderedOutput,
    target_path: Path,
    stacks: list[str],
    force: bool = False,
    preserve_context: bool = False,
    dry_run: bool = False,
    selected_options: dict[str, dict[str, str]] | None = None,
    profile_name: str | None = None,
) -> InstallResult:
    """
    Install rendered output to target directory.

    Args:
        output: Rendered templates and collected files
        target_path: Target project directory
        stacks: List of stack names being installed
        force: Overwrite existing .claude/ directory
        preserve_context: Keep context/ directory when using force
        dry_run: Only print what would be done, don't write files
        selected_options: Options selected for each stack {stack: {option: value}}
        profile_name: Profile name used for installation

    Returns:
        InstallResult with counts and any errors
    """
    result = InstallResult(target_path=target_path, dry_run=dry_run)

    # Validate target
    if not target_path.exists():
        result.errors.append(f"Target path does not exist: {target_path}")
        return result

    if not target_path.is_dir():
        result.errors.append(f"Target path is not a directory: {target_path}")
        return result

    claude_dir = target_path / ".claude"

    # Handle existing .claude/
    if claude_dir.exists():
        if not force:
            result.errors.append(".claude/ already exists. Use --force to overwrite.")
            return result

        if not dry_run:
            if preserve_context:
                # Remove everything except context/
                for item in claude_dir.iterdir():
                    if item.name != "context":
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
            else:
                shutil.rmtree(claude_dir)

    if dry_run:
        print(f"[DRY RUN] Would install to {target_path}")
        print(f"[DRY RUN] Stacks: {', '.join(stacks)}")

    # Create directory structure
    dirs_to_create = [
        claude_dir,
        claude_dir / "agents",
        claude_dir / "skills",
        claude_dir / "hooks",
        claude_dir / "context",
        claude_dir / "context" / "features",
    ]

    if output.patterns:
        dirs_to_create.append(claude_dir / "patterns")
    if output.styles:
        dirs_to_create.append(claude_dir / "styles")

    if not dry_run:
        for dir_path in dirs_to_create:
            ensure_directory(dir_path)

    # Install agents
    for filename, content in output.agents.items():
        agent_path = claude_dir / "agents" / filename
        if dry_run:
            print(f"[DRY RUN] Would write: {agent_path}")
        else:
            with open(agent_path, "w") as f:
                f.write(content)
        result.files_written.append(str(agent_path))
        result.agents_count += 1

    # Install skills
    for skill_name, source_dir in output.skills.items():
        skill_dst = claude_dir / "skills" / skill_name
        if dry_run:
            print(f"[DRY RUN] Would copy skill: {skill_name}")
        else:
            if skill_dst.exists():
                shutil.rmtree(skill_dst)
            shutil.copytree(source_dir, skill_dst)
        result.skills_count += 1

    # Install hooks
    for filename, source_path in output.hook_files.items():
        hook_dst = claude_dir / "hooks" / filename
        if dry_run:
            print(f"[DRY RUN] Would copy hook: {filename}")
        else:
            shutil.copy2(source_path, hook_dst)
            if filename.endswith(".sh"):
                make_executable(hook_dst)
        result.hooks_count += 1

    # Install patterns
    for filename, source_path in output.patterns.items():
        pattern_dst = claude_dir / "patterns" / filename
        if dry_run:
            print(f"[DRY RUN] Would copy pattern: {filename}")
        else:
            shutil.copy2(source_path, pattern_dst)
        result.patterns_count += 1

    # Install styles
    for filename, source_path in output.styles.items():
        style_dst = claude_dir / "styles" / filename
        if dry_run:
            print(f"[DRY RUN] Would copy style: {filename}")
        else:
            shutil.copy2(source_path, style_dst)
        result.styles_count += 1

    # Install settings.json
    settings_path = claude_dir / "settings.json"
    if dry_run:
        print(f"[DRY RUN] Would write: {settings_path}")
    else:
        with open(settings_path, "w") as f:
            json.dump(output.settings, f, indent=2)
            f.write("\n")
    result.files_written.append(str(settings_path))

    # Install CLAUDE.md to project root
    claude_md_path = target_path / "CLAUDE.md"
    if dry_run:
        print(f"[DRY RUN] Would write: {claude_md_path}")
    else:
        with open(claude_md_path, "w") as f:
            f.write(output.claude_md)
    result.files_written.append(str(claude_md_path))

    # Install README.md to .claude/
    readme_path = claude_dir / "README.md"
    if dry_run:
        print(f"[DRY RUN] Would write: {readme_path}")
    else:
        with open(readme_path, "w") as f:
            f.write(output.readme)
    result.files_written.append(str(readme_path))

    # Create .gitkeep files
    gitkeep_dirs = [
        claude_dir / "context" / "features",
    ]
    for gitkeep_dir in gitkeep_dirs:
        gitkeep_path = gitkeep_dir / ".gitkeep"
        if dry_run:
            print(f"[DRY RUN] Would create: {gitkeep_path}")
        else:
            ensure_directory(gitkeep_dir)
            gitkeep_path.touch()

    # Post-install tasks
    if not dry_run:
        # Create settings.local.json template
        create_settings_local_template(claude_dir)

        # Update .gitignore
        update_gitignore(target_path)

        # Make all .sh files executable
        for sh_file in claude_dir.rglob("*.sh"):
            make_executable(sh_file)

        # Create and save lock file
        lock = create_lock(
            stack_names=stacks,
            selected_options=selected_options or {},
            profile_name=profile_name,
        )

        # Compute checksums for installed files
        installed_files = []
        # Track relative paths from target_path
        for filename in output.agents:
            installed_files.append(f".claude/agents/{filename}")
        for skill_name in output.skills:
            # Add skill directory files
            skill_dir = claude_dir / "skills" / skill_name
            if skill_dir.exists():
                for f in skill_dir.rglob("*"):
                    if f.is_file():
                        installed_files.append(str(f.relative_to(target_path)))
        for filename in output.hook_files:
            installed_files.append(f".claude/hooks/{filename}")
        for filename in output.patterns:
            installed_files.append(f".claude/patterns/{filename}")
        for filename in output.styles:
            installed_files.append(f".claude/styles/{filename}")
        installed_files.append(".claude/settings.json")
        installed_files.append("CLAUDE.md")

        lock.file_checksums = compute_checksums(target_path, installed_files)
        save_lock(target_path, lock)
        result.lock = lock

    return result


def print_summary(result: InstallResult, stacks: list[str]) -> None:
    """
    Print installation summary.

    Args:
        result: Installation result
        stacks: List of stack names
    """
    prefix = "[DRY RUN] " if result.dry_run else ""

    print(f"\n{prefix}Installation Summary")
    print("─" * 40)
    print(f"Stacks:     {', '.join(stacks)}")
    print(f"Target:     {result.target_path}")
    print()
    print("Installed:")
    print(f"  Agents:   {result.agents_count}")
    print(f"  Skills:   {result.skills_count}")
    print(f"  Hooks:    {result.hooks_count}")
    print(f"  Patterns: {result.patterns_count}")
    print(f"  Styles:   {result.styles_count}")

    if result.errors:
        print()
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    else:
        print()
        print(f"{prefix}Bootstrap complete!")

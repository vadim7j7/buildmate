#!/usr/bin/env python3
"""
Buildmate - Bootstrap Claude Code agent configurations for your projects.

Usage:
    buildmate <stack> <target_path>
    buildmate rails ./my-rails-app
    buildmate rails+nextjs ./my-fullstack-app
    buildmate --profile saas ./my-app
    buildmate nextjs ./app --ui=tailwind --state=zustand
    buildmate --list
    buildmate --profiles
    buildmate --options nextjs
    buildmate --validate rails
"""

import argparse
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib import __version__
from lib.config import (
    compose_stacks,
    get_stack_options,
    list_available_profiles,
    list_available_stacks,
    load_profile,
    load_stack,
    parse_stack_arg,
)
from lib.installer import install, print_summary
from lib.lockfile import (
    get_modified_files,
    load_lock,
)
from lib.renderer import render_all
from lib.schema import validate_stack_file


def print_header():
    """Print the CLI header."""
    print()
    print(f"  Buildmate v{__version__}")
    print()


def cmd_list():
    """List available stacks."""
    print_header()
    stacks = list_available_stacks()

    if not stacks:
        print("No stacks found.")
        return 1

    print("Available stacks:")
    print()
    for stack_name in stacks:
        try:
            stack = load_stack(stack_name, validate=False)
            opts = f" [{len(stack.options)} options]" if stack.options else ""
            print(f"  {stack_name:20} {stack.display_name}{opts}")
        except Exception as e:
            print(f"  {stack_name:20} (error: {e})")

    print()
    print("Usage:")
    print("  python bootstrap.py <stack> <target_path>")
    print("  python bootstrap.py rails+nextjs ./my-app  # combine stacks")
    print("  python bootstrap.py --profile saas ./my-app  # use profile")
    print("  python bootstrap.py --options nextjs  # show stack options")
    print()
    return 0


def cmd_profiles():
    """List available profiles."""
    print_header()
    profiles = list_available_profiles()

    if not profiles:
        print("No profiles found.")
        print()
        print("Profiles are pre-defined stack combinations.")
        print("Create profiles in the profiles/ directory.")
        return 1

    print("Available profiles:")
    print()
    for profile_name in profiles:
        try:
            profile = load_profile(profile_name)
            stacks_str = "+".join(profile.stacks)
            print(f"  {profile_name:20} {profile.display_name}")
            print(f"  {'':<20} Stacks: {stacks_str}")
            if profile.options:
                for stack, opts in profile.options.items():
                    opts_str = ", ".join(f"{k}={v}" for k, v in opts.items())
                    print(f"  {'':<20} {stack}: {opts_str}")
            print()
        except Exception as e:
            print(f"  {profile_name:20} (error: {e})")

    print("Usage:")
    print("  python bootstrap.py --profile <name> <target_path>")
    print()
    return 0


def cmd_options(stack_name: str):
    """Show available options for a stack."""
    print_header()
    print(f"Options for stack: {stack_name}")
    print()

    try:
        options = get_stack_options(stack_name)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    if not options:
        print("This stack has no configurable options.")
        return 0

    for opt_name, option in options.items():
        print(f"  --{opt_name}=<choice>")
        print(f"      {option.description}")
        print(f"      Default: {option.default}")
        print("      Choices:")
        for choice_name, choice in option.choices.items():
            default_marker = " (default)" if choice_name == option.default else ""
            desc = f" - {choice.description}" if choice.description else ""
            print(f"        - {choice_name}{default_marker}{desc}")
        print()

    print("Usage:")
    print(
        f"  python bootstrap.py {stack_name} ./app --{list(options.keys())[0]}=<choice>"
    )
    print()
    return 0


def cmd_validate(stack_name: str):
    """Validate a stack configuration."""
    print_header()
    print(f"Validating stack: {stack_name}")
    print()

    from lib.config import STACKS_DIR

    stack_file = STACKS_DIR / stack_name / "stack.yaml"

    try:
        errors = validate_stack_file(stack_file, raise_on_error=False)
        if errors:
            print("Validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print("Validation passed!")
            return 0
    except FileNotFoundError:
        print(f"Stack not found: {stack_name}")
        return 1
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return 1


def parse_option_args(
    args: list[str], stack_names: list[str]
) -> dict[str, dict[str, str]]:
    """
    Parse option arguments like --ui=tailwind --state=zustand.

    Args:
        args: List of arguments to parse
        stack_names: List of stack names being used

    Returns:
        Dict of {stack_name: {option_name: choice}}
    """
    options: dict[str, dict[str, str]] = {}

    # Load all stack options to know which options belong to which stack
    stack_options_map: dict[str, dict[str, str]] = {}  # option_name -> stack_name
    for stack_name in stack_names:
        try:
            stack_opts = get_stack_options(stack_name)
            for opt_name in stack_opts:
                stack_options_map[opt_name] = stack_name
        except FileNotFoundError:
            pass

    for arg in args:
        if arg.startswith("--") and "=" in arg:
            # Parse --option=value
            key_value = arg[2:]  # Remove --
            if "=" in key_value:
                key, value = key_value.split("=", 1)
                # Find which stack this option belongs to
                if key in stack_options_map:
                    stack_name = stack_options_map[key]
                    if stack_name not in options:
                        options[stack_name] = {}
                    options[stack_name][key] = value

    return options


def cmd_bootstrap(
    stack_arg: str | None,
    target_path: Path,
    force: bool = False,
    preserve_context: bool = False,
    dry_run: bool = False,
    default_model: str | None = None,
    profile_name: str | None = None,
    extra_args: list[str] | None = None,
):
    """Bootstrap stacks to target directory."""
    print_header()

    # Load profile if specified
    profile = None
    if profile_name:
        try:
            profile = load_profile(profile_name)
            stack_names = profile.stacks
            print(f"Using profile: {profile.display_name}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
    else:
        # Parse stack argument
        if not stack_arg:
            print("Error: No stacks specified. Use --profile or provide stack names.")
            return 1
        stack_names = parse_stack_arg(stack_arg)
        if not stack_names:
            print("Error: No stacks specified")
            return 1

    # Parse extra option arguments
    cli_options = {}
    if extra_args:
        cli_options = parse_option_args(extra_args, stack_names)

    print(f"Bootstrapping: {', '.join(stack_names)}")
    print(f"Target: {target_path}")
    if dry_run:
        print("Mode: DRY RUN")
    print()

    # Validate target path
    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}")
        return 1

    if not target_path.is_dir():
        print(f"Error: Target path is not a directory: {target_path}")
        return 1

    # Check for existing .claude/
    claude_dir = target_path / ".claude"
    if claude_dir.exists() and not force:
        print(f"Error: {claude_dir} already exists")
        print("Use --force to overwrite")
        return 1

    # Load and compose stacks
    print("Loading stack configurations...")
    try:
        config = compose_stacks(
            stack_names,
            default_model=default_model,
            options=cli_options,
            profile=profile,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    print(f"  Stacks: {', '.join(s.display_name for s in config.stacks)}")
    print(f"  Agents: {len(config.all_agents)}")
    print(f"  Skills: {len(config.all_skills)}")

    # Show selected options
    if config.selected_options:
        print("  Options:")
        for stack_name, opts in config.selected_options.items():
            for opt_name, choice in opts.items():
                print(f"    {stack_name}.{opt_name}: {choice}")
    print()

    # Render templates
    print("Rendering templates...")
    try:
        output = render_all(config)
    except Exception as e:
        print(f"Error rendering templates: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print(f"  Rendered {len(output.agents)} agents")
    print()

    # Install to target
    print("Installing to target...")
    result = install(
        output=output,
        target_path=target_path,
        stacks=stack_names,
        force=force,
        preserve_context=preserve_context,
        dry_run=dry_run,
        selected_options=config.selected_options,
        profile_name=profile_name,
    )

    if result.errors:
        print()
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    # Print summary
    print_summary(result, stack_names)

    if not dry_run:
        print()
        print("Next steps:")
        print(f"  1. cd {target_path}")
        print("  2. Review CLAUDE.md and .claude/README.md")
        print("  3. Start using: 'Use PM: <task>' or slash commands")
        print()

    return 0


def cmd_add_stack(
    target_path: Path,
    stack_name: str,
    dry_run: bool = False,
    extra_args: list[str] | None = None,
):
    """Add a new stack to an existing project."""
    print_header()

    # Check that target has a lock file
    lock = load_lock(target_path)
    if not lock:
        print(f"Error: No bootstrap installation found at {target_path}")
        print("This command can only be used on projects bootstrapped with agents.")
        return 1

    # Check stack not already installed
    if lock.has_stack(stack_name):
        print(f"Error: Stack '{stack_name}' is already installed")
        print(f"Installed stacks: {', '.join(lock.get_stack_names())}")
        return 1

    # Validate the new stack
    try:
        load_stack(stack_name)
    except FileNotFoundError:
        print(f"Error: Stack not found: {stack_name}")
        return 1

    # Parse options for the new stack
    cli_options = {}
    if extra_args:
        cli_options = parse_option_args(extra_args, [stack_name])

    print(f"Adding stack: {stack_name}")
    print(f"Target: {target_path}")
    print(f"Existing stacks: {', '.join(lock.get_stack_names())}")
    if dry_run:
        print("Mode: DRY RUN")
    print()

    # Check for modified files
    modified = get_modified_files(target_path, lock)
    if modified:
        print("Warning: The following files have been modified since installation:")
        for f in modified:
            print(f"  - {f}")
        print()
        print("These files will be preserved. Only new stack files will be added.")
        print()

    # Compose all stacks (existing + new)
    all_stacks = lock.get_stack_names() + [stack_name]
    existing_options = lock.get_options()

    # Merge existing options with CLI options
    merged_options = {**existing_options, **cli_options}

    print("Loading stack configurations...")
    try:
        config = compose_stacks(
            all_stacks,
            options=merged_options,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return 1

    print(f"  All stacks: {', '.join(s.display_name for s in config.stacks)}")
    print()

    # Render templates
    print("Rendering templates...")
    try:
        output = render_all(config)
    except Exception as e:
        print(f"Error rendering templates: {e}")
        return 1

    # Install (with force to update existing files, preserving context)
    print("Installing to target...")
    result = install(
        output=output,
        target_path=target_path,
        stacks=all_stacks,
        force=True,
        preserve_context=True,
        dry_run=dry_run,
        selected_options=config.selected_options,
        profile_name=lock.profile,
    )

    if result.errors:
        print()
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    # Print summary
    print_summary(result, all_stacks)

    if not dry_run:
        print()
        print(f"Successfully added '{stack_name}' to project!")
        print()

    return 0


def cmd_set_option(
    target_path: Path,
    option_spec: str,
    dry_run: bool = False,
):
    """Change an option for an existing stack."""
    print_header()

    # Parse option_spec: "stack.option=value"
    if "=" not in option_spec:
        print("Error: Option format should be: stack.option=value")
        print("Example: nextjs.ui=tailwind")
        return 1

    key_part, value = option_spec.split("=", 1)
    if "." not in key_part:
        print("Error: Option format should be: stack.option=value")
        print("Example: nextjs.ui=tailwind")
        return 1

    stack_name, option_name = key_part.split(".", 1)

    # Check that target has a lock file
    lock = load_lock(target_path)
    if not lock:
        print(f"Error: No bootstrap installation found at {target_path}")
        return 1

    # Check stack is installed
    if not lock.has_stack(stack_name):
        print(f"Error: Stack '{stack_name}' is not installed")
        print(f"Installed stacks: {', '.join(lock.get_stack_names())}")
        return 1

    # Validate the option exists
    try:
        stack_opts = get_stack_options(stack_name)
    except FileNotFoundError:
        print(f"Error: Stack not found: {stack_name}")
        return 1

    if option_name not in stack_opts:
        print(f"Error: Option '{option_name}' not found for stack '{stack_name}'")
        print(f"Available options: {', '.join(stack_opts.keys())}")
        return 1

    # Validate the value is valid
    option_def = stack_opts[option_name]
    if value not in option_def.choices:
        print(f"Error: Invalid value '{value}' for option '{option_name}'")
        print(f"Valid choices: {', '.join(option_def.choices.keys())}")
        return 1

    print(f"Setting option: {stack_name}.{option_name}={value}")
    print(f"Target: {target_path}")
    if dry_run:
        print("Mode: DRY RUN")
    print()

    # Check for modified files
    modified = get_modified_files(target_path, lock)
    if modified:
        print("Warning: The following files have been modified since installation:")
        for f in modified:
            print(f"  - {f}")
        print()

    # Build options with the new value
    all_stacks = lock.get_stack_names()
    updated_options = lock.get_options()

    if stack_name not in updated_options:
        updated_options[stack_name] = {}
    updated_options[stack_name][option_name] = value

    print("Loading stack configurations...")
    try:
        config = compose_stacks(
            all_stacks,
            options=updated_options,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return 1

    print()

    # Render templates
    print("Rendering templates...")
    try:
        output = render_all(config)
    except Exception as e:
        print(f"Error rendering templates: {e}")
        return 1

    # Install (with force, preserving context)
    print("Installing to target...")
    result = install(
        output=output,
        target_path=target_path,
        stacks=all_stacks,
        force=True,
        preserve_context=True,
        dry_run=dry_run,
        selected_options=config.selected_options,
        profile_name=lock.profile,
    )

    if result.errors:
        print()
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    # Print summary
    print_summary(result, all_stacks)

    if not dry_run:
        print()
        print(f"Successfully changed {stack_name}.{option_name} to '{value}'!")
        print()

    return 0


def cmd_upgrade(
    target_path: Path,
    dry_run: bool = False,
):
    """Upgrade an existing project to the latest templates."""
    print_header()

    # Check that target has a lock file
    lock = load_lock(target_path)
    if not lock:
        print(f"Error: No bootstrap installation found at {target_path}")
        return 1

    print(f"Upgrading: {target_path}")
    print(f"Installed stacks: {', '.join(lock.get_stack_names())}")
    print(f"Original version: {lock.version}")
    print(f"Current version: {__version__}")
    if lock.profile:
        print(f"Profile: {lock.profile}")
    if dry_run:
        print("Mode: DRY RUN")
    print()

    # Check for modified files
    modified = get_modified_files(target_path, lock)
    if modified:
        print("Warning: The following files have been modified since installation:")
        for f in modified:
            print(f"  - {f}")
        print()
        print("These files will be overwritten with the latest templates.")
        print("Consider backing them up first.")
        print()

    # Rebuild with the same stacks and options
    all_stacks = lock.get_stack_names()
    all_options = lock.get_options()

    print("Loading stack configurations...")
    try:
        config = compose_stacks(
            all_stacks,
            options=all_options,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return 1

    print(f"  Stacks: {', '.join(s.display_name for s in config.stacks)}")
    print()

    # Render templates
    print("Rendering templates...")
    try:
        output = render_all(config)
    except Exception as e:
        print(f"Error rendering templates: {e}")
        return 1

    # Install (with force, preserving context)
    print("Installing to target...")
    result = install(
        output=output,
        target_path=target_path,
        stacks=all_stacks,
        force=True,
        preserve_context=True,
        dry_run=dry_run,
        selected_options=config.selected_options,
        profile_name=lock.profile,
    )

    if result.errors:
        print()
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    # Print summary
    print_summary(result, all_stacks)

    if not dry_run:
        print()
        print(f"Successfully upgraded from v{lock.version} to v{__version__}!")
        print()

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bootstrap Claude Code agent configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bootstrap.py rails ./my-rails-app
  python bootstrap.py nextjs ./my-nextjs-app
  python bootstrap.py rails+nextjs ./my-fullstack-app
  python bootstrap.py --profile saas ./my-app
  python bootstrap.py nextjs ./app --ui=tailwind --state=zustand
  python bootstrap.py --list
  python bootstrap.py --profiles
  python bootstrap.py --options nextjs
  python bootstrap.py --validate rails

Extend existing projects:
  python bootstrap.py --add-stack react-native ./my-app --state=zustand
  python bootstrap.py --set-option nextjs.ui=tailwind ./my-app
  python bootstrap.py --upgrade ./my-app
        """,
    )

    parser.add_argument(
        "stack",
        nargs="?",
        help="Stack name(s) to bootstrap (use + to combine: rails+nextjs)",
    )
    parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        help="Target project directory",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available stacks",
    )
    parser.add_argument(
        "--profiles",
        action="store_true",
        help="List available profiles",
    )
    parser.add_argument(
        "--profile",
        metavar="NAME",
        help="Use a pre-defined profile",
    )
    parser.add_argument(
        "--options",
        metavar="STACK",
        help="Show available options for a stack",
    )
    parser.add_argument(
        "--validate",
        metavar="STACK",
        help="Validate a stack configuration",
    )
    parser.add_argument(
        "--add-stack",
        metavar="STACK",
        help="Add a stack to an existing project",
    )
    parser.add_argument(
        "--set-option",
        metavar="STACK.OPT=VAL",
        help="Change an option for an existing stack (e.g., nextjs.ui=tailwind)",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Upgrade an existing project to the latest templates",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .claude/ directory",
    )
    parser.add_argument(
        "--preserve-context",
        action="store_true",
        help="Keep context/ directory when using --force",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be done without writing files",
    )
    parser.add_argument(
        "--default-model",
        choices=["opus", "sonnet", "haiku"],
        help="Override default model for all agents",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Parse known args and collect unknown args (for dynamic options)
    args, unknown_args = parser.parse_known_args()

    # Handle --list
    if args.list:
        return cmd_list()

    # Handle --profiles
    if args.profiles:
        return cmd_profiles()

    # Handle --options
    if args.options:
        return cmd_options(args.options)

    # Handle --validate
    if args.validate:
        return cmd_validate(args.validate)

    # Handle --add-stack
    if args.add_stack:
        target = args.target or (Path(args.stack) if args.stack else None)
        if not target:
            parser.error("--add-stack requires a target path")
        return cmd_add_stack(
            target_path=target,
            stack_name=args.add_stack,
            dry_run=args.dry_run,
            extra_args=unknown_args,
        )

    # Handle --set-option
    if args.set_option:
        target = args.target or (Path(args.stack) if args.stack else None)
        if not target:
            parser.error("--set-option requires a target path")
        return cmd_set_option(
            target_path=target,
            option_spec=args.set_option,
            dry_run=args.dry_run,
        )

    # Handle --upgrade
    if args.upgrade:
        target = args.target or (Path(args.stack) if args.stack else None)
        if not target:
            parser.error("--upgrade requires a target path")
        return cmd_upgrade(
            target_path=target,
            dry_run=args.dry_run,
        )

    # Handle case where profile is used: first positional becomes target
    target = args.target
    stack = args.stack

    if args.profile and not target and stack:
        # When --profile is used, the first positional arg is the target, not stack
        target = Path(stack)
        stack = None

    # Require target for bootstrap
    if not target:
        parser.print_help()
        return 1

    if not stack and not args.profile:
        parser.error("Either stack or --profile is required")

    return cmd_bootstrap(
        stack_arg=stack,
        target_path=target,
        force=args.force,
        preserve_context=args.preserve_context,
        dry_run=args.dry_run,
        default_model=args.default_model,
        profile_name=args.profile,
        extra_args=unknown_args,
    )


if __name__ == "__main__":
    sys.exit(main())

"""
Stack configuration loading and management.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .schema import validate_stack_config, check_compatibility, check_agent_conflicts


# Paths
V2_ROOT = Path(__file__).parent.parent
STACKS_DIR = V2_ROOT / "stacks"
BASE_DIR = V2_ROOT / "base"
PROFILES_DIR = V2_ROOT / "profiles"


@dataclass
class QualityGate:
    """Quality gate configuration."""
    name: str
    command: str
    fix_command: str | None = None
    description: str | None = None


@dataclass
class Agent:
    """Agent configuration."""
    name: str
    template: str
    tools: list[str]
    description: str = ""
    model: str | None = None  # None means use stack default
    skills: list[str] = field(default_factory=list)  # Skills this agent can use
    memory: str | None = None  # Memory scope: user, project, or local


@dataclass
class OptionChoice:
    """A single choice within a stack option."""
    name: str
    description: str = ""
    patterns: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "OptionChoice":
        """Create OptionChoice from a dictionary."""
        return cls(
            name=name,
            description=data.get("description", ""),
            patterns=data.get("patterns", []),
            styles=data.get("styles", []),
            skills=data.get("skills", []),
            variables=data.get("variables", {}),
        )


@dataclass
class StackOption:
    """A configurable option for a stack (e.g., state management, UI library)."""
    name: str
    description: str
    default: str
    choices: dict[str, OptionChoice]

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "StackOption":
        """Create StackOption from a dictionary."""
        choices = {
            choice_name: OptionChoice.from_dict(choice_name, choice_data)
            for choice_name, choice_data in data.get("choices", {}).items()
        }
        return cls(
            name=name,
            description=data.get("description", ""),
            default=data.get("default", ""),
            choices=choices,
        )


@dataclass
class StackConfig:
    """Complete stack configuration."""
    name: str
    display_name: str
    description: str
    default_model: str
    compatible_with: list[str]
    agents: list[Agent]
    skills: list[str]
    quality_gates: dict[str, QualityGate]
    working_dir: str
    patterns: list[str]
    styles: list[str]
    variables: dict[str, Any]
    options: dict[str, StackOption] = field(default_factory=dict)

    # Internal - path to the stack directory
    stack_path: Path = field(default_factory=Path)

    @classmethod
    def from_dict(cls, data: dict[str, Any], stack_path: Path) -> "StackConfig":
        """Create StackConfig from a dictionary (parsed YAML)."""
        agents = [
            Agent(
                name=a["name"],
                template=a["template"],
                tools=a["tools"],
                description=a.get("description", ""),
                model=a.get("model"),
                skills=a.get("skills", []),
                memory=a.get("memory"),
            )
            for a in data.get("agents", [])
        ]

        quality_gates = {
            name: QualityGate(
                name=name,
                command=gate["command"],
                fix_command=gate.get("fix_command"),
                description=gate.get("description"),
            )
            for name, gate in data.get("quality_gates", {}).items()
        }

        options = {
            opt_name: StackOption.from_dict(opt_name, opt_data)
            for opt_name, opt_data in data.get("options", {}).items()
        }

        return cls(
            name=data["name"],
            display_name=data["display_name"],
            description=data.get("description", ""),
            default_model=data.get("default_model", "sonnet"),
            compatible_with=data.get("compatible_with", []),
            agents=agents,
            skills=data.get("skills", []),
            quality_gates=quality_gates,
            working_dir=data.get("working_dir", "."),
            patterns=data.get("patterns", []),
            styles=data.get("styles", []),
            variables=data.get("variables", {}),
            options=options,
            stack_path=stack_path,
        )


@dataclass
class Profile:
    """Pre-defined stack combination with options."""
    name: str
    display_name: str
    description: str
    stacks: list[str]
    options: dict[str, dict[str, str]]  # stack_name -> option_name -> choice
    variables: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Profile":
        """Create Profile from a dictionary (parsed YAML)."""
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            description=data.get("description", ""),
            stacks=data.get("stacks", []),
            options=data.get("options", {}),
            variables=data.get("variables", {}),
        )


@dataclass
class ComposedConfig:
    """Composed configuration from multiple stacks."""
    stacks: list[StackConfig]
    all_agents: list[Agent]
    all_skills: list[str]
    all_quality_gates: dict[str, dict[str, QualityGate]]  # stack_name -> gate_name -> gate
    all_patterns: dict[str, Path]  # filename -> full path
    all_styles: dict[str, Path]  # filename -> full path
    variables: dict[str, Any]
    default_model: str
    selected_options: dict[str, dict[str, str]] = field(default_factory=dict)  # stack -> option -> choice


def list_available_stacks() -> list[str]:
    """List all available stack names."""
    stacks = []
    for stack_dir in STACKS_DIR.iterdir():
        if stack_dir.is_dir() and (stack_dir / "stack.yaml").exists():
            stacks.append(stack_dir.name)
    return sorted(stacks)


def list_available_profiles() -> list[str]:
    """List all available profile names."""
    profiles = []
    if PROFILES_DIR.exists():
        for profile_file in PROFILES_DIR.glob("*.yaml"):
            profiles.append(profile_file.stem)
    return sorted(profiles)


def load_stack(stack_name: str, validate: bool = True) -> StackConfig:
    """
    Load a single stack configuration.

    Args:
        stack_name: Name of the stack (directory name)
        validate: Whether to validate against JSON schema

    Returns:
        StackConfig object

    Raises:
        FileNotFoundError: If stack doesn't exist
        ValidationError: If validation fails
    """
    stack_path = STACKS_DIR / stack_name
    config_file = stack_path / "stack.yaml"

    if not config_file.exists():
        available = list_available_stacks()
        raise FileNotFoundError(
            f"Stack '{stack_name}' not found. Available stacks: {', '.join(available)}"
        )

    with open(config_file) as f:
        raw_config = yaml.safe_load(f)

    if validate:
        validate_stack_config(raw_config, raise_on_error=True)

    return StackConfig.from_dict(raw_config, stack_path)


def load_profile(profile_name: str) -> Profile:
    """
    Load a profile configuration.

    Args:
        profile_name: Name of the profile (filename without .yaml)

    Returns:
        Profile object

    Raises:
        FileNotFoundError: If profile doesn't exist
    """
    profile_file = PROFILES_DIR / f"{profile_name}.yaml"

    if not profile_file.exists():
        available = list_available_profiles()
        if available:
            raise FileNotFoundError(
                f"Profile '{profile_name}' not found. Available profiles: {', '.join(available)}"
            )
        else:
            raise FileNotFoundError(
                f"Profile '{profile_name}' not found. No profiles directory exists."
            )

    with open(profile_file) as f:
        raw_config = yaml.safe_load(f)

    return Profile.from_dict(raw_config)


def load_stacks(stack_names: list[str], validate: bool = True) -> list[StackConfig]:
    """
    Load multiple stack configurations.

    Args:
        stack_names: List of stack names to load
        validate: Whether to validate each stack

    Returns:
        List of StackConfig objects
    """
    return [load_stack(name, validate=validate) for name in stack_names]


def get_stack_options(stack_name: str) -> dict[str, StackOption]:
    """
    Get available options for a stack.

    Args:
        stack_name: Name of the stack

    Returns:
        Dictionary of option_name -> StackOption
    """
    stack = load_stack(stack_name, validate=False)
    return stack.options


def apply_options(
    stack: StackConfig,
    selected_options: dict[str, str],
) -> tuple[list[str], list[str], list[str], dict[str, Any]]:
    """
    Apply selected options to get additional patterns, styles, skills, and variables.

    Args:
        stack: Stack configuration
        selected_options: Map of option_name -> selected choice

    Returns:
        Tuple of (patterns, styles, skills, variables) from selected options
    """
    extra_patterns: list[str] = []
    extra_styles: list[str] = []
    extra_skills: list[str] = []
    extra_variables: dict[str, Any] = {}

    for opt_name, option in stack.options.items():
        # Use provided selection or default
        choice_name = selected_options.get(opt_name, option.default)

        if choice_name not in option.choices:
            available = list(option.choices.keys())
            raise ValueError(
                f"Invalid choice '{choice_name}' for option '{opt_name}' in stack '{stack.name}'. "
                f"Available: {', '.join(available)}"
            )

        choice = option.choices[choice_name]
        extra_patterns.extend(choice.patterns)
        extra_styles.extend(choice.styles)
        extra_skills.extend(choice.skills)
        extra_variables.update(choice.variables)

    return extra_patterns, extra_styles, extra_skills, extra_variables


def compose_stacks(
    stack_names: list[str],
    default_model: str | None = None,
    validate: bool = True,
    options: dict[str, dict[str, str]] | None = None,
    profile: Profile | None = None,
) -> ComposedConfig:
    """
    Compose multiple stacks into a single configuration.

    Args:
        stack_names: List of stack names to compose
        default_model: Override default model for all stacks
        validate: Whether to validate configurations
        options: Option selections per stack {stack_name: {option_name: choice}}
        profile: Profile to apply (provides default options)

    Returns:
        ComposedConfig with merged agents, skills, etc.

    Raises:
        ValueError: If stacks are incompatible or invalid options
    """
    # Merge options from profile and explicit options (explicit wins)
    merged_options: dict[str, dict[str, str]] = {}
    if profile:
        merged_options = dict(profile.options)
    if options:
        for stack_name, stack_opts in options.items():
            if stack_name not in merged_options:
                merged_options[stack_name] = {}
            merged_options[stack_name].update(stack_opts)

    # Load all stacks
    stacks = load_stacks(stack_names, validate=validate)

    # Check compatibility
    if len(stacks) > 1:
        raw_configs = []
        for name in stack_names:
            config_file = STACKS_DIR / name / "stack.yaml"
            with open(config_file) as f:
                raw_configs.append(yaml.safe_load(f))

        errors = check_compatibility(raw_configs)
        if errors:
            raise ValueError("Stack compatibility errors:\n" + "\n".join(errors))

        warnings = check_agent_conflicts(raw_configs)
        for warning in warnings:
            print(f"Warning: {warning}")

    # Merge agents (later stacks override earlier ones)
    agent_map: dict[str, Agent] = {}
    for stack in stacks:
        for agent in stack.agents:
            # Apply stack default model if agent doesn't specify one
            if agent.model is None:
                agent.model = default_model or stack.default_model
            agent_map[agent.name] = agent

    # Merge skills (deduplicated)
    skill_set: set[str] = set()
    for stack in stacks:
        skill_set.update(stack.skills)

    # Collect quality gates by stack
    all_quality_gates: dict[str, dict[str, QualityGate]] = {}
    for stack in stacks:
        all_quality_gates[stack.name] = stack.quality_gates

    # Collect patterns and styles
    all_patterns: dict[str, Path] = {}
    all_styles: dict[str, Path] = {}

    # Merge variables
    merged_variables: dict[str, Any] = {}

    # Track selected options for output
    selected_options: dict[str, dict[str, str]] = {}

    for stack in stacks:
        # Add base patterns
        for pattern in stack.patterns:
            pattern_path = stack.stack_path / pattern
            if pattern_path.exists():
                all_patterns[pattern_path.name] = pattern_path

        # Add base styles
        for style in stack.styles:
            style_path = stack.stack_path / style
            if style_path.exists():
                all_styles[style_path.name] = style_path

        # Add base variables
        merged_variables.update(stack.variables)

        # Apply options if stack has any
        if stack.options:
            stack_opts = merged_options.get(stack.name, {})
            extra_patterns, extra_styles, extra_skills, extra_vars = apply_options(
                stack, stack_opts
            )

            # Add option-based patterns
            for pattern in extra_patterns:
                pattern_path = stack.stack_path / pattern
                if pattern_path.exists():
                    all_patterns[pattern_path.name] = pattern_path

            # Add option-based styles
            for style in extra_styles:
                style_path = stack.stack_path / style
                if style_path.exists():
                    all_styles[style_path.name] = style_path

            # Add option-based skills
            skill_set.update(extra_skills)

            # Add option-based variables
            merged_variables.update(extra_vars)

            # Track what was selected
            selected_options[stack.name] = {
                opt_name: stack_opts.get(opt_name, opt.default)
                for opt_name, opt in stack.options.items()
            }

    # Add profile variables
    if profile:
        merged_variables.update(profile.variables)

    # Determine default model
    final_default_model = default_model or stacks[0].default_model

    return ComposedConfig(
        stacks=stacks,
        all_agents=list(agent_map.values()),
        all_skills=sorted(skill_set),
        all_quality_gates=all_quality_gates,
        all_patterns=all_patterns,
        all_styles=all_styles,
        variables=merged_variables,
        default_model=final_default_model,
        selected_options=selected_options,
    )


def parse_stack_arg(stack_arg: str) -> list[str]:
    """
    Parse stack argument which may contain comma-separated or plus-separated stack names.

    Args:
        stack_arg: Stack argument like "rails", "rails,nextjs", or "rails+nextjs"

    Returns:
        List of stack names
    """
    # Support both comma and plus separators
    if "+" in stack_arg:
        return [s.strip() for s in stack_arg.split("+") if s.strip()]
    return [s.strip() for s in stack_arg.split(",") if s.strip()]

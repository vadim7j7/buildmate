"""
JSON Schema validation for stack configurations.
"""

import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, ValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    ValidationError = Exception  # type: ignore


# Path to the schema file
SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "stack.schema.json"


def load_schema() -> dict[str, Any]:
    """Load the stack configuration JSON schema."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_stack_config(
    config: dict[str, Any], raise_on_error: bool = True
) -> list[str]:
    """
    Validate a stack configuration against the JSON schema.

    Args:
        config: The stack configuration dictionary to validate
        raise_on_error: If True, raise ValidationError on first error.
                       If False, return list of all error messages.

    Returns:
        List of error messages (empty if valid)

    Raises:
        ValidationError: If raise_on_error is True and validation fails
        ImportError: If jsonschema is not installed
    """
    if not HAS_JSONSCHEMA:
        raise ImportError(
            "jsonschema package is required for validation. "
            "Install it with: pip install jsonschema"
        )

    schema = load_schema()
    validator = Draft202012Validator(schema)

    errors: list[str] = []

    for error in validator.iter_errors(config):
        error_path = (
            " -> ".join(str(p) for p in error.absolute_path)
            if error.absolute_path
            else "root"
        )
        error_msg = f"[{error_path}] {error.message}"
        errors.append(error_msg)

        if raise_on_error:
            raise ValidationError(error_msg)

    return errors


def validate_stack_file(yaml_path: Path, raise_on_error: bool = True) -> list[str]:
    """
    Load and validate a stack.yaml file.

    Args:
        yaml_path: Path to the stack.yaml file
        raise_on_error: If True, raise on first error

    Returns:
        List of error messages (empty if valid)
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML package is required. Install it with: pip install pyyaml"
        )

    if not yaml_path.exists():
        raise FileNotFoundError(f"Stack config not found: {yaml_path}")

    with open(yaml_path) as f:
        config = yaml.safe_load(f)

    if config.get("extends"):
        from .config import _resolve_inheritance

        config, _ = _resolve_inheritance(config, yaml_path.parent)

    return validate_stack_config(config, raise_on_error=raise_on_error)


def check_compatibility(stack_configs: list[dict[str, Any]]) -> list[str]:
    """
    Check if multiple stacks are compatible with each other.

    Args:
        stack_configs: List of stack configuration dictionaries

    Returns:
        List of incompatibility error messages (empty if all compatible)
    """
    if len(stack_configs) < 2:
        return []

    errors: list[str] = []

    def lists(config: dict[str, Any], other: dict[str, Any]) -> bool:
        """True if config declares other (or other's parent) compatible."""
        compatible_with = config.get("compatible_with") or []
        return other["name"] in compatible_with or (
            bool(other.get("extends")) and other["extends"] in compatible_with
        )

    # A pair is compatible when either side declares it (directly or via the
    # other's parent stack), so a new stack only has to list its partners once.
    for i, config in enumerate(stack_configs):
        for other in stack_configs[i + 1 :]:
            if not (lists(config, other) or lists(other, config)):
                errors.append(
                    f"Stack '{config['name']}' is not compatible with "
                    f"'{other['name']}'. Add '{other['name']}' to compatible_with "
                    f"in {config['name']}/stack.yaml"
                )

    return errors


def check_agent_conflicts(stack_configs: list[dict[str, Any]]) -> list[str]:
    """
    Check for agent name conflicts across multiple stacks.

    Args:
        stack_configs: List of stack configuration dictionaries

    Returns:
        List of conflict warnings (conflicts are allowed but warned)
    """
    warnings: list[str] = []
    agent_sources: dict[str, str] = {}

    for config in stack_configs:
        stack_name = config["name"]
        for agent in config.get("agents", []):
            agent_name = agent["name"]
            if agent_name in agent_sources:
                warnings.append(
                    f"Agent '{agent_name}' defined in both '{agent_sources[agent_name]}' "
                    f"and '{stack_name}'. The latter will override."
                )
            agent_sources[agent_name] = stack_name

    return warnings


# Stack sub-folders the installer reads (scaffold is configurable, see stack.yaml)
KNOWN_STACK_DIRS = {"agents", "skills", "patterns", "styles", "hooks", "scaffold"}


def check_stack_files(
    stack_dir: Path, config: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """
    Check that a stack's referenced files exist and that its files are referenced.

    Looks at ``patterns:``, ``styles:`` and ``skills:`` at the top level, in
    agents, and in option choices. A referenced pattern or style must exist in
    the stack or its parent; a referenced skill must exist in the stack, its
    parent or ``base/skills``. Files and skill folders on disk that nothing
    references are reported as warnings, as are directories the installer
    never reads (any folder other than agents, skills, patterns, styles,
    hooks, scaffold).

    Args:
        stack_dir: Path to ``stacks/<name>``
        config: The stack's raw stack.yaml content

    Returns:
        (errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []
    stacks_root = stack_dir.parent
    parent_dir = stacks_root / config["extends"] if config.get("extends") else None
    base_skills = stacks_root.parent / "base" / "skills"

    def references(cfg: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
        pats = set(cfg.get("patterns") or []) | set(cfg.get("reference_patterns") or [])
        stys = set(cfg.get("styles") or [])
        skls = set(cfg.get("skills") or [])
        for agent in cfg.get("agents") or []:
            skls.update(agent.get("skills") or [])
        for option in (cfg.get("options") or {}).values():
            for choice in (option.get("choices") or {}).values():
                choice = choice or {}
                pats.update(choice.get("patterns") or [])
                stys.update(choice.get("styles") or [])
                skls.update(choice.get("skills") or [])
        return pats, stys, skls

    patterns, styles, skills = references(config)

    # A child may override a file or skill its parent references (same path)
    if parent_dir and (parent_dir / "stack.yaml").exists():
        import yaml

        parent_config = yaml.safe_load((parent_dir / "stack.yaml").read_text()) or {}
        p_pats, p_stys, p_skls = references(parent_config)
        patterns |= p_pats
        styles |= p_stys
        skills |= p_skls

    def exists(rel: str) -> bool:
        return (stack_dir / rel).exists() or bool(
            parent_dir and (parent_dir / rel).exists()
        )

    for rel in sorted(patterns | styles):
        if not exists(rel):
            errors.append(f"Referenced file not found: {rel}")
    for skill in sorted(skills):
        if not any(
            exists(f"skills/{skill}/{name}") or (base_skills / skill / name).exists()
            for name in ("SKILL.md", "SKILL.md.j2")
        ):
            errors.append(f"Skill '{skill}' has no SKILL.md (stack, parent or base)")

    for kind, referenced in (("patterns", patterns), ("styles", styles)):
        folder = stack_dir / kind
        if folder.is_dir():
            for f in sorted(folder.iterdir()):
                if (
                    f.is_file()
                    and not f.name.startswith(".")
                    and f"{kind}/{f.name}" not in referenced
                ):
                    warnings.append(f"Unreferenced file: {kind}/{f.name}")

    # Skills a child stack may reference from this stack (when this is a parent)
    child_skills: set[str] = set()
    for other in stacks_root.iterdir():
        other_yaml = other / "stack.yaml"
        if other.is_dir() and other_yaml.exists() and other != stack_dir:
            try:
                import yaml

                other_config = yaml.safe_load(other_yaml.read_text()) or {}
            except Exception:
                continue
            if other_config.get("extends") == stack_dir.name:
                child_skills.update(other_config.get("skills") or [])
                for agent in other_config.get("agents") or []:
                    child_skills.update(agent.get("skills") or [])

    skills_dir = stack_dir / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and d.name not in skills and d.name not in child_skills:
                warnings.append(f"Unreferenced skill: skills/{d.name}")

    for folder in sorted(stack_dir.iterdir()):
        if folder.is_dir() and folder.name not in KNOWN_STACK_DIRS:
            warnings.append(
                f"{folder.name}/ is never installed (lib/ does not read it)"
            )

    return errors, warnings

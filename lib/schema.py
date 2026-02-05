"""
JSON Schema validation for stack configurations.
"""

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema
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


def validate_stack_config(config: dict[str, Any], raise_on_error: bool = True) -> list[str]:
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
        error_path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
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
    stack_names = [s["name"] for s in stack_configs]

    for config in stack_configs:
        name = config["name"]
        compatible_with = config.get("compatible_with", [])

        for other_name in stack_names:
            if other_name != name and other_name not in compatible_with:
                errors.append(
                    f"Stack '{name}' is not compatible with '{other_name}'. "
                    f"Add '{other_name}' to compatible_with in {name}/stack.yaml"
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

"""
Jinja2 template rendering for agent configurations.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import BASE_DIR, V2_ROOT, ComposedConfig, StackConfig


@dataclass
class RenderedOutput:
    """Container for all rendered output."""

    agents: dict[str, str] = field(default_factory=dict)  # filename -> content
    claude_md: str = ""
    readme: str = ""
    settings: dict[str, Any] = field(default_factory=dict)
    patterns: dict[str, Path] = field(default_factory=dict)  # filename -> source path
    styles: dict[str, Path] = field(default_factory=dict)  # filename -> source path
    skills: dict[str, Path] = field(default_factory=dict)  # skill_name -> source dir
    hooks: dict[str, str] = field(
        default_factory=dict
    )  # filename -> content (or path if not template)
    hook_files: dict[str, Path] = field(
        default_factory=dict
    )  # filename -> source path (non-template)
    services_config: dict[str, Any] | None = None  # services.json for dashboard


def create_jinja_env(template_dirs: list[Path]) -> Environment:
    """
    Create a Jinja2 environment with custom filters.

    Args:
        template_dirs: List of directories to search for templates

    Returns:
        Configured Jinja2 Environment
    """
    env = Environment(
        loader=FileSystemLoader([str(d) for d in template_dirs]),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add custom filters
    env.filters["basename"] = lambda path: os.path.basename(path)

    # Filter to find agent by role (developer, tester, reviewer)
    def find_agent_by_role(agents: list, role: str):
        """Find first agent whose name contains the given role."""
        for agent in agents:
            if role in agent.name:
                return agent
        return None

    env.filters["find_by_role"] = find_agent_by_role

    # Test to check if string contains substring
    env.tests["contains"] = lambda value, substring: substring in value

    return env


def build_template_context(
    config: ComposedConfig, dashboard: bool = False
) -> dict[str, Any]:
    """
    Build the context dictionary for template rendering.

    Args:
        config: Composed configuration from multiple stacks
        dashboard: Whether MCP Dashboard is enabled

    Returns:
        Dictionary of variables available in templates
    """
    return {
        # Stack information
        "stacks": config.stacks,
        "stack": config.stacks[0] if len(config.stacks) == 1 else None,
        # Merged data
        "all_agents": config.all_agents,
        "all_skills": config.all_skills,
        "all_quality_gates": config.all_quality_gates,
        "all_patterns": config.all_patterns,
        "all_styles": config.all_styles,
        # Global settings
        "default_model": config.default_model,
        "variables": config.variables,
        # Dashboard integration
        "dashboard": dashboard,
    }


def render_base_agents(env: Environment, context: dict[str, Any]) -> dict[str, str]:
    """
    Render base agent templates (orchestrator, grind, eval, security).

    Args:
        env: Jinja2 environment
        context: Template context

    Returns:
        Dictionary of filename -> rendered content
    """
    agents = {}
    base_agents_dir = BASE_DIR / "agents"

    for template_file in base_agents_dir.glob("*.md.j2"):
        template = env.get_template(f"base/agents/{template_file.name}")
        output_name = template_file.name.replace(".j2", "")
        agents[output_name] = template.render(**context)

    return agents


def render_stack_agents(
    env: Environment,
    context: dict[str, Any],
    stack: StackConfig,
) -> dict[str, str]:
    """
    Render stack-specific agent templates.

    Args:
        env: Jinja2 environment
        context: Template context
        stack: Stack configuration

    Returns:
        Dictionary of filename -> rendered content
    """
    agents = {}

    for agent in stack.agents:
        template_path = f"stacks/{stack.name}/{agent.template}"

        # Add agent-specific context
        agent_context = {
            **context,
            "agent": agent,
            "stack": stack,
        }

        try:
            template = env.get_template(template_path)
            output_name = f"{agent.name}.md"
            agents[output_name] = template.render(**agent_context)
        except Exception as e:
            print(f"Warning: Failed to render {template_path}: {e}")

    return agents


def render_claude_md(env: Environment, context: dict[str, Any]) -> str:
    """
    Render the main CLAUDE.md file.

    Args:
        env: Jinja2 environment
        context: Template context

    Returns:
        Rendered CLAUDE.md content
    """
    template = env.get_template("base/CLAUDE.md.j2")
    return template.render(**context)


def render_readme(env: Environment, context: dict[str, Any]) -> str:
    """
    Render the .claude/README.md file.

    Args:
        env: Jinja2 environment
        context: Template context

    Returns:
        Rendered README.md content
    """
    template = env.get_template("base/README.md.j2")
    return template.render(**context)


def collect_skills(config: ComposedConfig) -> dict[str, Path]:
    """
    Collect all skill directories from base and stacks.

    Args:
        config: Composed configuration

    Returns:
        Dictionary of skill_name -> source directory path
    """
    skills = {}

    # Base skills (always included)
    base_skills_dir = BASE_DIR / "skills"
    if base_skills_dir.exists():
        for skill_dir in base_skills_dir.iterdir():
            if skill_dir.is_dir():
                skills[skill_dir.name] = skill_dir

    # Stack-specific skills
    for stack in config.stacks:
        stack_skills_dir = stack.stack_path / "skills"
        if stack_skills_dir.exists():
            for skill_name in stack.skills:
                skill_dir = stack_skills_dir / skill_name
                if skill_dir.exists():
                    skills[skill_name] = skill_dir

    return skills


def collect_hooks(config: ComposedConfig) -> tuple[dict[str, str], dict[str, Path]]:
    """
    Collect hook files, rendering templates and collecting static files.

    Args:
        config: Composed configuration

    Returns:
        Tuple of (rendered_hooks, static_hook_files)
    """
    rendered = {}
    static = {}

    # Base hooks
    base_hooks_dir = BASE_DIR / "hooks"
    if base_hooks_dir.exists():
        for hook_file in base_hooks_dir.iterdir():
            if hook_file.is_file():
                if hook_file.suffix == ".j2":
                    # This is a template - will be rendered later
                    pass
                else:
                    static[hook_file.name] = hook_file

    # Stack-specific hooks (override base)
    for stack in config.stacks:
        stack_hooks_dir = stack.stack_path / "hooks"
        if stack_hooks_dir.exists():
            for hook_file in stack_hooks_dir.iterdir():
                if hook_file.is_file():
                    static[hook_file.name] = hook_file

    return rendered, static


def render_all(config: ComposedConfig, dashboard: bool = False) -> RenderedOutput:
    """
    Render all templates for a composed configuration.

    Args:
        config: Composed configuration from one or more stacks
        dashboard: Whether MCP Dashboard is enabled

    Returns:
        RenderedOutput containing all rendered content
    """
    # Set up Jinja2 environment with all template directories
    template_dirs = [V2_ROOT]  # Root so we can use paths like "base/agents/..."

    env = create_jinja_env(template_dirs)
    context = build_template_context(config, dashboard=dashboard)

    output = RenderedOutput()

    # Render base agents
    output.agents.update(render_base_agents(env, context))

    # Render stack-specific agents
    for stack in config.stacks:
        output.agents.update(render_stack_agents(env, context, stack))

    # Render CLAUDE.md and README
    output.claude_md = render_claude_md(env, context)
    output.readme = render_readme(env, context)

    # Collect patterns and styles (copy as-is, no rendering)
    output.patterns = config.all_patterns
    output.styles = config.all_styles

    # Collect skills
    output.skills = collect_skills(config)

    # Collect hooks
    output.hooks, output.hook_files = collect_hooks(config)

    # Load base settings
    import json

    settings_file = BASE_DIR / "settings.json"
    if settings_file.exists():
        with open(settings_file) as f:
            output.settings = json.load(f)

    # Generate services.json config for dashboard
    if dashboard:
        import yaml

        svc_list = []
        for stack in config.stacks:
            # Read raw YAML to get verification section (not on StackConfig)
            raw_yaml_path = stack.stack_path / "stack.yaml"
            if raw_yaml_path.exists():
                with open(raw_yaml_path) as f:
                    raw = yaml.safe_load(f)
                verification = raw.get("verification", {})
                dev_server = verification.get("dev_server", {})
                command = dev_server.get("command")
                if command:
                    port = dev_server.get("port") or stack.variables.get("dev_port")
                    svc_list.append(
                        {
                            "id": stack.name,
                            "name": f"{stack.display_name} Dev Server",
                            "command": command,
                            "cwd": stack.working_dir,
                            "port": int(port) if port else None,
                        }
                    )
        if svc_list:
            output.services_config = {"services": svc_list}

    # Auto-populate multi_repo config for multi-stack compositions
    if len(config.stacks) > 1:
        if "pm" not in output.settings:
            output.settings["pm"] = {}
        output.settings["pm"]["multi_repo"] = {
            "enabled": True,
            "repositories": {
                s.working_dir: f"./{s.working_dir}" for s in config.stacks
            },
            "stack_repo_map": {
                s.name: s.working_dir for s in config.stacks
            },
        }

    return output

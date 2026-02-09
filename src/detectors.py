from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

from .models import RepoFeatures


def detect_claude_md(tree_paths: set[str], features: RepoFeatures) -> None:
    """Detect CLAUDE.md files at root or nested."""
    for path in tree_paths:
        if PurePosixPath(path).name == "CLAUDE.md":
            features.has_claude_md = True
            return


def detect_claude_dir(tree_paths: set[str], features: RepoFeatures) -> None:
    """Detect .claude/ directory."""
    for path in tree_paths:
        if path == ".claude" or path.startswith(".claude/"):
            features.has_claude_dir = True
            return


def detect_custom_commands(tree_paths: set[str], features: RepoFeatures) -> None:
    """Detect skills in .claude/commands/ and .claude/skills/ directories."""
    commands_prefix = ".claude/commands/"
    skills_prefix = ".claude/skills/"
    for path in tree_paths:
        if path.startswith(commands_prefix) and path != commands_prefix:
            name = PurePosixPath(path).stem
            if name not in features.custom_commands:
                features.custom_commands.append(name)
        elif path.startswith(skills_prefix) and path != skills_prefix:
            # Skills use directory-based structure: .claude/skills/<name>/SKILL.md
            parts = path[len(skills_prefix):].split("/")
            name = parts[0]
            if name not in features.custom_commands:
                features.custom_commands.append(name)
    if features.custom_commands:
        features.has_custom_commands = True


def detect_memory(tree_paths: set[str], features: RepoFeatures) -> None:
    """Detect MEMORY.md files."""
    for path in tree_paths:
        if PurePosixPath(path).name == "MEMORY.md":
            features.has_memory = True
            return


def detect_agents(tree_paths: set[str], features: RepoFeatures) -> None:
    """Detect Claude agent files in .claude/agents/ directory."""
    prefix = ".claude/agents/"
    for path in tree_paths:
        if path.startswith(prefix) and path != prefix:
            name = PurePosixPath(path).stem
            if name not in features.agent_names:
                features.agent_names.append(name)
    if features.agent_names:
        features.has_agents = True


# ---------------------------------------------------------------------------
# Content-needed detectors: return paths that need content fetching
# ---------------------------------------------------------------------------

def paths_needing_content(tree_paths: set[str]) -> dict[str, list[str]]:
    """Return a dict mapping detector names to file paths that need content.

    Keys: 'mcp_json', 'settings_json', 'workflows'
    """
    result: dict[str, list[str]] = {"mcp_json": [], "settings_json": [], "workflows": []}

    for path in tree_paths:
        if PurePosixPath(path).name == ".mcp.json":
            result["mcp_json"].append(path)
        if path == ".claude/settings.json":
            result["settings_json"].append(path)
        if path.startswith(".github/workflows/") and (path.endswith(".yml") or path.endswith(".yaml")):
            result["workflows"].append(path)

    return result


def parse_mcp_json_content(content: str, features: RepoFeatures) -> None:
    """Parse .mcp.json content to extract MCP server names."""
    try:
        data = json.loads(content)
        servers = data.get("mcpServers", {})
        if isinstance(servers, dict):
            for name in servers:
                if name not in features.mcp_servers:
                    features.mcp_servers.append(name)
    except (json.JSONDecodeError, AttributeError):
        return


def parse_settings_json_content(content: str, features: RepoFeatures) -> None:
    """Parse .claude/settings.json to extract MCP servers and hooks."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, AttributeError):
        return

    # MCP servers
    servers = data.get("mcpServers", {})
    if isinstance(servers, dict):
        for name in servers:
            if name not in features.mcp_servers:
                features.mcp_servers.append(name)

    # Hooks
    hooks = data.get("hooks", {})
    if isinstance(hooks, dict):
        for hook_type, hook_list in hooks.items():
            if isinstance(hook_list, list) and len(hook_list) > 0:
                features.has_hooks = True
                if hook_type not in features.hook_types:
                    features.hook_types.append(hook_type)


# Claude-related patterns in workflow files
_CLAUDE_ACTION_PATTERNS = [
    (re.compile(r"anthropics/claude-code-action", re.IGNORECASE), "claude-code-action"),
    (re.compile(r"anthropics/claude-code-base-action", re.IGNORECASE), "claude-code-base-action"),
    (re.compile(r"claude-code", re.IGNORECASE), "claude-code (ref)"),
]


def parse_workflow_content(content: str, features: RepoFeatures) -> None:
    """Parse GitHub workflow YAML content for Claude-related references."""
    for pattern, name in _CLAUDE_ACTION_PATTERNS:
        if pattern.search(content):
            if name not in features.claude_action_names:
                features.claude_action_names.append(name)
            features.has_claude_actions = True

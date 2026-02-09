from __future__ import annotations

from collections import Counter

from .config import Config
from .graph import make_graph
from .models import OrgStats


def _format_row(label: str, count: int, total: int, config: Config, show_bar: bool = True) -> str:
    """Format a single row, optionally with a bar chart."""
    if total == 0:
        percent = 0.0
    else:
        percent = count / total * 100
    if show_bar:
        bar = make_graph(percent, bar_length=config.bar_length, blocks=config.blocks)
        return f"{label:<22}{count:>3} repos   {bar}  {percent:5.2f} %"
    return f"{label:<22}{count:>3} repos"


def _render_ranked(
    title: str,
    counter: Counter,
    total: int,
    config: Config,
    show_bar: bool = True,
) -> list[str]:
    """Render a ranked section from a Counter."""
    if not counter:
        return []
    lines = [f"\n{title}"]
    for name, count in counter.most_common(config.max_items):
        if show_bar:
            percent = count / total * 100 if total > 0 else 0
            bar = make_graph(percent, bar_length=config.bar_length, blocks=config.blocks)
            lines.append(f"{name:<22}{count:>3} repos   {bar}  {percent:5.2f} %")
        else:
            lines.append(f"{name:<22}{count:>3} repos")
    return lines


def _render_adoption(stats: OrgStats, config: Config, show_bar: bool = True) -> list[str]:
    """Render the adoption overview section."""
    items = [
        ("Has CLAUDE.md", stats.claude_md_count),
        ("Has .claude/ Dir", stats.claude_dir_count),
        ("Has MCP Servers", stats.mcp_servers_count),
        ("Has Skills", stats.custom_commands_count),
        ("Has Claude Actions", stats.claude_actions_count),
        ("Has Hooks", stats.hooks_count),
        ("Has Agents", stats.agents_count),
        ("Has Memory", stats.memory_count),
    ]
    # Only show items with count > 0
    items = [(label, count) for label, count in items if count > 0]
    lines = [f"📊 Claude Code Adoption ({stats.total_repos} repos scanned)", ""]
    if not items:
        lines.append("No Claude Code features detected across repos.")
        return lines

    for label, count in items:
        lines.append(_format_row(label, count, stats.total_repos, config, show_bar))
    return lines


def _render_details(stats: OrgStats, _config: Config) -> list[str]:
    """Render per-repo detail table."""
    if not stats.repos:
        return []

    # Only include repos with at least one feature
    active_repos = [r for r in stats.repos if any([
        r.has_claude_md, r.has_claude_dir, r.has_mcp_servers,
        r.has_custom_commands, r.has_claude_actions, r.has_hooks,
        r.has_agents, r.has_memory,
    ])]
    if not active_repos:
        return []

    headers = ["Repo", "CLAUDE.md", ".claude/", "MCP", "Skills", "Actions", "Hooks", "Agents", "Memory"]
    lines = [
        "\n<details>",
        "<summary>Per-repo breakdown</summary>",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    def check(val: bool) -> str:
        return "✅" if val else ""

    for repo in sorted(active_repos, key=lambda r: r.name.lower()):
        row = [
            repo.name,
            check(repo.has_claude_md),
            check(repo.has_claude_dir),
            check(repo.has_mcp_servers),
            check(repo.has_custom_commands),
            check(repo.has_claude_actions),
            check(repo.has_hooks),
            check(repo.has_agents),
            check(repo.has_memory),
        ]
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append("</details>")
    return lines


# Chart sections return raw lines (no code fences); render_stats wraps them.
# Each value is a callable(stats, config, show_bar) -> list[str].
_CHART_SECTIONS = {
    "adoption": lambda stats, config, show_bar: _render_adoption(stats, config, show_bar),
    "mcp": lambda stats, config, show_bar: _render_ranked(
        f"🔧 Top MCP Servers (of {stats.mcp_servers_count} repos with MCP)",
        stats.mcp_server_counter,
        stats.mcp_servers_count,
        config,
        show_bar,
    ),
    "skills": lambda stats, config, show_bar: _render_ranked(
        f"⚡ Top Skills (of {stats.custom_commands_count} repos)",
        stats.custom_command_counter,
        stats.custom_commands_count,
        config,
        show_bar,
    ),
    "actions": lambda stats, config, show_bar: _render_ranked(
        f"🤖 Top GitHub Actions (of {stats.claude_actions_count} repos)",
        stats.claude_action_counter,
        stats.claude_actions_count,
        config,
        show_bar,
    ),
    "hooks": lambda stats, config, show_bar: _render_ranked(
        f"🪝 Top Hooks (of {stats.hooks_count} repos)",
        stats.hook_type_counter,
        stats.hooks_count,
        config,
        show_bar,
    ),
    "agents": lambda stats, config, show_bar: _render_ranked(
        f"🕵️ Top Agents (of {stats.agents_count} repos)",
        stats.agent_name_counter,
        stats.agents_count,
        config,
        show_bar,
    ),
}

# Non-chart sections rendered outside the code block.
_OTHER_SECTIONS = {
    "details": lambda stats, config: _render_details(stats, config),
}


def render_stats(stats: OrgStats, config: Config) -> str:
    """Render all configured sections into a markdown string."""
    chart_lines: list[str] = []
    other_lines: list[str] = []

    for section in config.show_sections:
        if section in _CHART_SECTIONS:
            show_bar = section in config.bar_sections
            lines = _CHART_SECTIONS[section](stats, config, show_bar)
            if lines:
                chart_lines.extend(lines)
        elif section in _OTHER_SECTIONS:
            lines = _OTHER_SECTIONS[section](stats, config)
            if lines:
                other_lines.extend(lines)

    result_parts: list[str] = []
    if chart_lines:
        result_parts.append("```\n" + "\n".join(chart_lines) + "\n```")
    if other_lines:
        result_parts.append("\n".join(other_lines))

    return "\n".join(result_parts)

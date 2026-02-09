from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter


@dataclass
class RepoFeatures:
    name: str
    has_claude_md: bool = False
    has_claude_dir: bool = False
    has_custom_commands: bool = False
    has_claude_actions: bool = False
    has_hooks: bool = False
    has_agents: bool = False
    has_memory: bool = False
    mcp_servers: list[str] = field(default_factory=list)
    custom_commands: list[str] = field(default_factory=list)
    claude_action_names: list[str] = field(default_factory=list)
    hook_types: list[str] = field(default_factory=list)

    @property
    def has_mcp_servers(self) -> bool:
        return len(self.mcp_servers) > 0


@dataclass
class OrgStats:
    org_name: str
    total_repos: int = 0
    repos: list[RepoFeatures] = field(default_factory=list)

    # Aggregated counts
    claude_md_count: int = 0
    claude_dir_count: int = 0
    mcp_servers_count: int = 0
    custom_commands_count: int = 0
    claude_actions_count: int = 0
    hooks_count: int = 0
    agents_count: int = 0
    memory_count: int = 0

    # Detailed breakdowns
    mcp_server_counter: Counter = field(default_factory=Counter)
    custom_command_counter: Counter = field(default_factory=Counter)
    claude_action_counter: Counter = field(default_factory=Counter)
    hook_type_counter: Counter = field(default_factory=Counter)

    @staticmethod
    def aggregate(org_name: str, repos: list[RepoFeatures]) -> OrgStats:
        stats = OrgStats(org_name=org_name, total_repos=len(repos), repos=repos)
        for repo in repos:
            if repo.has_claude_md:
                stats.claude_md_count += 1
            if repo.has_claude_dir:
                stats.claude_dir_count += 1
            if repo.has_mcp_servers:
                stats.mcp_servers_count += 1
            if repo.has_custom_commands:
                stats.custom_commands_count += 1
            if repo.has_claude_actions:
                stats.claude_actions_count += 1
            if repo.has_hooks:
                stats.hooks_count += 1
            if repo.has_agents:
                stats.agents_count += 1
            if repo.has_memory:
                stats.memory_count += 1

            for server in repo.mcp_servers:
                stats.mcp_server_counter[server] += 1
            for cmd in repo.custom_commands:
                stats.custom_command_counter[cmd] += 1
            for action in repo.claude_action_names:
                stats.claude_action_counter[action] += 1
            for hook in repo.hook_types:
                stats.hook_type_counter[hook] += 1

        return stats

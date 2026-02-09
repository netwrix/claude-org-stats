from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    gh_token: str
    org_name: str
    repository: str = ""
    show_sections: list[str] = field(default_factory=lambda: ["adoption", "mcp"])
    blocks: str = "░█"
    bar_length: int = 25
    max_items: int = 10
    exclude_archived: bool = True
    exclude_forks: bool = True
    exclude_repos: list[str] = field(default_factory=list)
    section_name: str = "claude-stats"
    target_path: str = "README.md"
    target_branch: str = ""
    commit_message: str = "Update Claude Code adoption stats"
    committer_name: str = "github-actions[bot]"
    committer_email: str = "github-actions[bot]@users.noreply.github.com"

    @staticmethod
    def from_env() -> Config:
        def get(name: str, default: str = "") -> str:
            return os.environ.get(f"INPUT_{name}", os.environ.get(name, default))

        sections_raw = get("SHOW_SECTIONS", "adoption,mcp")
        sections = [s.strip() for s in sections_raw.split(",") if s.strip()]

        exclude_raw = get("EXCLUDE_REPOS", "")
        exclude = [r.strip() for r in exclude_raw.split(",") if r.strip()]

        return Config(
            gh_token=get("GH_TOKEN"),
            org_name=get("ORG_NAME"),
            repository=get("REPOSITORY"),
            show_sections=sections,
            blocks=get("BLOCKS", "░█"),
            bar_length=int(get("BAR_LENGTH", "25")),
            max_items=int(get("MAX_ITEMS", "10")),
            exclude_archived=get("EXCLUDE_ARCHIVED", "true").lower() == "true",
            exclude_forks=get("EXCLUDE_FORKS", "true").lower() == "true",
            exclude_repos=exclude,
            section_name=get("SECTION_NAME", "claude-stats"),
            target_path=get("TARGET_PATH", "README.md"),
            target_branch=get("TARGET_BRANCH", ""),
            commit_message=get("COMMIT_MESSAGE", "Update Claude Code adoption stats"),
            committer_name=get("COMMITTER_NAME", "github-actions[bot]"),
            committer_email=get("COMMITTER_EMAIL", "github-actions[bot]@users.noreply.github.com"),
        )

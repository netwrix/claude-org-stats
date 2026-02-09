from __future__ import annotations

import datetime
import time

from github import Auth, Github, GithubException

from .config import Config
from .models import OrgStats, RepoFeatures
from .detectors import (
    detect_agents,
    detect_claude_dir,
    detect_claude_md,
    detect_custom_commands,
    detect_memory,
    parse_mcp_json_content,
    parse_settings_json_content,
    parse_workflow_content,
    paths_needing_content,
)


def _check_rate_limit(gh: Github, threshold: int = 10) -> None:
    """Sleep until rate limit resets if remaining calls are below threshold."""
    rate = gh.get_rate_limit().rate
    if rate.remaining < threshold:
        sleep_time = max(0, (rate.reset - datetime.datetime.now(
            datetime.timezone.utc
        )).total_seconds()) + 5
        print(f"Rate limit low ({rate.remaining} remaining). Sleeping {sleep_time:.0f}s...")
        time.sleep(sleep_time)


def _get_file_content(repo, path: str) -> str | None:
    """Fetch a single file's content from a repo."""
    try:
        content_file = repo.get_contents(path)
        if hasattr(content_file, "decoded_content"):
            return content_file.decoded_content.decode("utf-8", errors="replace")
    except GithubException:
        pass
    return None


def scan_repo(gh: Github, repo) -> RepoFeatures:
    """Scan a single repository for Claude Code features."""
    features = RepoFeatures(name=repo.name)

    _check_rate_limit(gh)

    # Get full tree in one API call
    try:
        default_branch = repo.default_branch
        tree = repo.get_git_tree(default_branch, recursive=True)
    except GithubException:
        # Empty repo or other error
        return features

    tree_paths = {item.path for item in tree.tree}

    # Tree-based detectors (no API calls needed)
    detect_claude_md(tree_paths, features)
    detect_claude_dir(tree_paths, features)
    detect_custom_commands(tree_paths, features)
    detect_memory(tree_paths, features)
    detect_agents(tree_paths, features)

    # Content-based detectors (need file contents)
    needed = paths_needing_content(tree_paths)

    for path in needed["mcp_json"]:
        content = _get_file_content(repo, path)
        if content:
            parse_mcp_json_content(content, features)

    for path in needed["settings_json"]:
        content = _get_file_content(repo, path)
        if content:
            parse_settings_json_content(content, features)

    for path in needed["workflows"]:
        content = _get_file_content(repo, path)
        if content:
            parse_workflow_content(content, features)

    return features


def scan_organization(config: Config) -> OrgStats:
    """Scan all repos in an organization for Claude Code features."""
    gh = Github(auth=Auth.Token(config.gh_token))
    org = gh.get_organization(config.org_name)

    repos_data: list[RepoFeatures] = []
    exclude_set = set(config.exclude_repos)

    print(f"Scanning organization: {config.org_name}")

    for repo in org.get_repos(type="all", sort="full_name"):
        if config.exclude_archived and repo.archived:
            continue
        if config.exclude_forks and repo.fork:
            continue
        if repo.name in exclude_set:
            continue

        print(f"  Scanning {repo.name}...")
        features = scan_repo(gh, repo)
        repos_data.append(features)

    print(f"Scanned {len(repos_data)} repos.")
    return OrgStats.aggregate(config.org_name, repos_data)

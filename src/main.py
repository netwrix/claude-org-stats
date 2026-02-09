from __future__ import annotations

import re
import sys

from github import Auth, Github, GithubException, InputGitAuthor

from .config import Config
from .renderer import render_stats
from .scanner import scan_organization


def _replace_section(readme: str, section_name: str, content: str) -> str:
    """Replace content between section markers in README."""
    start_marker = f"<!--START_SECTION:{section_name}-->"
    end_marker = f"<!--END_SECTION:{section_name}-->"

    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )

    replacement = f"{start_marker}\n{content}\n{end_marker}"

    if pattern.search(readme):
        return pattern.sub(replacement, readme)

    # Markers not found - return unchanged
    print(f"Warning: Section markers for '{section_name}' not found in README.")
    return readme


def update_readme(config: Config, rendered: str) -> None:
    """Update the README file in the repository with rendered stats."""
    gh = Github(auth=Auth.Token(config.gh_token))

    # Determine the repository to update
    if config.repository:
        repo = gh.get_repo(config.repository)
    else:
        repo = gh.get_repo(f"{config.org_name}/{config.org_name}")

    # Determine branch
    branch = config.target_branch or repo.default_branch

    # Get current README
    try:
        readme_file = repo.get_contents(config.target_path, ref=branch)
    except GithubException as e:
        print(f"Error: Could not read {config.target_path}: {e}")
        sys.exit(1)

    current_content = readme_file.decoded_content.decode("utf-8")
    new_content = _replace_section(current_content, config.section_name, rendered)

    if new_content == current_content:
        print("No changes to README. Skipping commit.")
        return

    # Commit the update
    committer = InputGitAuthor(config.committer_name, config.committer_email)
    repo.update_file(
        path=config.target_path,
        message=config.commit_message,
        content=new_content,
        sha=readme_file.sha,
        branch=branch,
        committer=committer,
    )
    print(f"Updated {config.target_path} on {branch}.")


def main() -> None:
    config = Config.from_env()

    if not config.gh_token:
        print("Error: GH_TOKEN is required.")
        sys.exit(1)
    if not config.org_name:
        print("Error: ORG_NAME is required.")
        sys.exit(1)

    stats = scan_organization(config)
    rendered = render_stats(stats, config)

    print("\n--- Rendered Output ---")
    print(rendered)
    print("--- End Output ---\n")

    update_readme(config, rendered)


if __name__ == "__main__":
    main()

from collections import Counter

from src.config import Config
from src.models import OrgStats, RepoFeatures
from src.renderer import render_stats
from src.main import _replace_section


def _make_config(**overrides) -> Config:
    defaults = dict(
        gh_token="fake",
        org_name="test-org",
        show_sections=["adoption", "mcp"],
        blocks="░█",
        bar_length=25,
        max_items=10,
    )
    defaults.update(overrides)
    return Config(**defaults)


def _make_stats() -> OrgStats:
    repos = [
        RepoFeatures(name="repo-a", has_claude_md=True, mcp_servers=["filesystem", "github"]),
        RepoFeatures(name="repo-b", has_claude_md=True, has_claude_dir=True, mcp_servers=["filesystem"]),
        RepoFeatures(name="repo-c", has_claude_actions=True, claude_action_names=["claude-code-action"]),
        RepoFeatures(name="repo-d"),
    ]
    return OrgStats.aggregate("test-org", repos)


class TestRenderStats:
    def test_adoption_section(self):
        stats = _make_stats()
        config = _make_config(show_sections=["adoption"])
        result = render_stats(stats, config)
        assert "4 repos scanned" in result
        assert "Has CLAUDE.md" in result
        assert "50.00 %" in result

    def test_mcp_section(self):
        stats = _make_stats()
        config = _make_config(show_sections=["mcp"])
        result = render_stats(stats, config)
        assert "Top MCP Servers" in result
        assert "filesystem" in result
        assert "github" in result

    def test_both_sections_single_code_block(self):
        stats = _make_stats()
        config = _make_config(show_sections=["adoption", "mcp"])
        result = render_stats(stats, config)
        assert "Claude Code Adoption" in result
        assert "Top MCP Servers" in result
        # All chart sections should be in one code block (exactly one pair of fences)
        assert result.count("```") == 2

    def test_empty_stats(self):
        stats = OrgStats.aggregate("test-org", [])
        config = _make_config(show_sections=["adoption"])
        result = render_stats(stats, config)
        assert "0 repos scanned" in result

    def test_details_section(self):
        stats = _make_stats()
        config = _make_config(show_sections=["details"])
        result = render_stats(stats, config)
        assert "Per-repo breakdown" in result
        assert "repo-a" in result
        assert "repo-d" not in result  # no features
        assert ".claude/" in result  # .claude/ column present

    def test_custom_bar_length(self):
        stats = _make_stats()
        config = _make_config(show_sections=["adoption"], bar_length=10)
        result = render_stats(stats, config)
        # Bar should be shorter
        assert "█" in result

    def test_no_mcp_section_when_empty(self):
        repos = [RepoFeatures(name="repo-a", has_claude_md=True)]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["mcp"])
        result = render_stats(stats, config)
        assert "Top MCP Servers" not in result


class TestReplaceSection:
    def test_basic_replacement(self):
        readme = """# My Repo

<!--START_SECTION:claude-stats-->
old content
<!--END_SECTION:claude-stats-->

## Footer
"""
        result = _replace_section(readme, "claude-stats", "new content")
        assert "new content" in result
        assert "old content" not in result
        assert "## Footer" in result
        assert "<!--START_SECTION:claude-stats-->" in result
        assert "<!--END_SECTION:claude-stats-->" in result

    def test_missing_markers(self):
        readme = "# My Repo\n\nNo markers here."
        result = _replace_section(readme, "claude-stats", "content")
        assert result == readme

    def test_custom_section_name(self):
        readme = """<!--START_SECTION:my-stats-->
old
<!--END_SECTION:my-stats-->"""
        result = _replace_section(readme, "my-stats", "new")
        assert "new" in result
        assert "old" not in result

    def test_multiline_content(self):
        readme = """<!--START_SECTION:claude-stats-->
line1
line2
<!--END_SECTION:claude-stats-->"""
        new_content = "a\nb\nc"
        result = _replace_section(readme, "claude-stats", new_content)
        assert "a\nb\nc" in result

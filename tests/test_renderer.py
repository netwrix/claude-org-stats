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
        assert "repo-d" in result  # All repos shown (including those without features)
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

    def test_no_bars_shows_counts_only(self):
        stats = _make_stats()
        config = _make_config(show_sections=["adoption"], bar_sections=[])
        result = render_stats(stats, config)
        assert "Has CLAUDE.md" in result
        assert "2 repos" in result
        assert "░" not in result
        assert "█" not in result
        assert "%" not in result

    def test_bars_enabled_by_default(self):
        stats = _make_stats()
        config = _make_config(show_sections=["adoption"])
        result = render_stats(stats, config)
        assert "█" in result
        assert "%" in result

    def test_mixed_bar_sections(self):
        stats = _make_stats()
        config = _make_config(show_sections=["adoption", "mcp"], bar_sections=["adoption"])
        result = render_stats(stats, config)
        # Adoption should have bars
        assert "50.00 %" in result
        # MCP should just have counts (no percentage after server names)
        lines = result.split("\n")
        mcp_lines = [l for l in lines if "filesystem" in l]
        assert len(mcp_lines) == 1
        assert "%" not in mcp_lines[0]


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


class TestRenderStatsDetailedOutput:
    """Test that rendered output contains correct data and formatting."""

    def test_detail_table_has_correct_columns(self):
        """Verify the detail table has all required columns in correct order."""
        repos = [
            RepoFeatures(name="test-repo", has_claude_md=True),
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["details"])
        result = render_stats(stats, config)

        # Check header row includes new "New" and "Stale" columns
        assert "| Repo | CLAUDE.md | .claude/ | MCP | Skills | Actions | Hooks | Agents | Memory | New | Stale |" in result

    def test_detail_table_shows_all_repos(self):
        """All repos should appear in detail table, including those without features."""
        repos = [
            RepoFeatures(name="active-repo", has_claude_md=True),
            RepoFeatures(name="empty-repo"),
            RepoFeatures(name="another-active", has_agents=True),
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["details"])
        result = render_stats(stats, config)

        assert "active-repo" in result
        assert "another-active" in result
        assert "empty-repo" in result  # All repos shown now

    def test_detail_table_checkmarks(self):
        """Verify checkmarks appear for enabled features."""
        repos = [
            RepoFeatures(
                name="full-featured",
                has_claude_md=True,
                has_claude_dir=True,
                has_custom_commands=True,
                has_claude_actions=True,
                has_hooks=True,
                has_agents=True,
                has_memory=True,
                mcp_servers=["filesystem"],
                custom_commands=["review"],
                claude_action_names=["claude-code-action"],
                hook_types=["PreToolUse"],
            ),
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["details"])
        result = render_stats(stats, config)

        # Should have 8 checkmarks (one for each feature column)
        assert result.count("✅") == 8

    def test_detail_table_new_and_stale_indicators(self):
        """Verify new and stale indicators appear in detail table."""
        repos = [
            RepoFeatures(name="new-repo", is_new=True, has_claude_md=True),
            RepoFeatures(name="stale-repo", is_stale=True, has_claude_dir=True),
            RepoFeatures(name="normal-repo", has_agents=True),
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["details"])
        result = render_stats(stats, config)

        # Should have 1 new indicator (🆕) and 1 stale indicator (⚠️)
        assert result.count("🆕") == 1
        assert result.count("⚠️") == 1
        # Verify they appear in correct rows
        assert "new-repo" in result
        assert "stale-repo" in result
        assert "normal-repo" in result

    def test_adoption_only_shows_features_with_nonzero_count(self):
        """Adoption section should only show features that exist in at least one repo."""
        repos = [
            RepoFeatures(name="repo1", has_claude_md=True),
            RepoFeatures(name="repo2", has_claude_md=True),
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["adoption"])
        result = render_stats(stats, config)

        assert "Has CLAUDE.md" in result
        # Features with 0 count should not appear
        assert "Has MCP Servers" not in result
        assert "Has Custom Commands" not in result
        assert "Has Claude Actions" not in result
        assert "Has Hooks" not in result
        assert "Has Agents" not in result
        assert "Has Memory" not in result

    def test_all_sections_together(self):
        """Test rendering all sections together."""
        repos = [
            RepoFeatures(
                name="repo1",
                has_claude_md=True,
                mcp_servers=["filesystem"],
                custom_commands=["review"],
                claude_action_names=["claude-code-action"],
                hook_types=["PreToolUse"],
            ),
            RepoFeatures(name="repo2", has_claude_md=True),
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(
            show_sections=["adoption", "mcp", "skills", "actions", "hooks", "details"]
        )
        result = render_stats(stats, config)

        # Check all sections appear
        assert "Claude Code Adoption" in result
        assert "Top MCP Servers" in result
        assert "Top Skills" in result
        assert "Top GitHub Actions" in result
        assert "Top Hooks" in result
        assert "Per-repo breakdown" in result

    def test_mcp_percentage_relative_to_mcp_repos(self):
        """MCP server percentages should be relative to repos with MCP, not all repos."""
        repos = [
            RepoFeatures(name="repo1", mcp_servers=["filesystem", "github"]),
            RepoFeatures(name="repo2", mcp_servers=["filesystem"]),
            RepoFeatures(name="repo3"),  # No MCP
            RepoFeatures(name="repo4"),  # No MCP
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["mcp"], bar_sections=["mcp"])
        result = render_stats(stats, config)

        # filesystem: 2/2 MCP repos = 100%
        # github: 1/2 MCP repos = 50%
        lines = result.split("\n")
        filesystem_line = [l for l in lines if "filesystem" in l][0]
        github_line = [l for l in lines if "github" in l][0]

        assert "100.00 %" in filesystem_line
        assert "50.00 %" in github_line

    def test_skills_section_uses_correct_denominator(self):
        """Skills/commands percentages should be relative to repos with commands."""
        repos = [
            RepoFeatures(
                name="repo1",
                has_custom_commands=True,
                custom_commands=["review", "test"],
            ),
            RepoFeatures(
                name="repo2",
                has_custom_commands=True,
                custom_commands=["review"],
            ),
            RepoFeatures(name="repo3"),  # No commands
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["skills"])
        result = render_stats(stats, config)

        # review: 2/2 command repos = 100%
        # test: 1/2 command repos = 50%
        lines = result.split("\n")
        review_line = [l for l in lines if "review" in l][0]
        test_line = [l for l in lines if "test" in l][0]

        assert "100.00 %" in review_line
        assert "50.00 %" in test_line

    def test_zero_total_repos_no_division_error(self):
        """Ensure no division by zero when total repos is 0."""
        stats = OrgStats.aggregate("test-org", [])
        config = _make_config(show_sections=["adoption"])
        result = render_stats(stats, config)

        assert "0 repos scanned" in result
        # Should not raise any exceptions

    def test_details_section_with_no_repos(self):
        """Test details section returns nothing when there are no repos."""
        stats = OrgStats.aggregate("test-org", [])
        config = _make_config(show_sections=["details"])
        result = render_stats(stats, config)

        # Should be empty (no content)
        assert result == ""

    def test_details_section_with_only_inactive_repos(self):
        """Test details section when all repos have no features."""
        repos = [
            RepoFeatures(name="empty1"),
            RepoFeatures(name="empty2"),
        ]
        stats = OrgStats.aggregate("test-org", repos)
        config = _make_config(show_sections=["details"])
        result = render_stats(stats, config)

        # Should still show all repos, even those without features
        assert "Per-repo breakdown" in result
        assert "empty1" in result
        assert "empty2" in result

    def test_format_row_with_zero_total(self):
        """Test _format_row handles total=0 without division error."""
        from src.renderer import _format_row
        config = _make_config()

        # Should not raise division by zero
        result = _format_row("Test Label", 0, 0, config, show_bar=True)
        assert "0.00 %" in result
        assert "0 repos" in result

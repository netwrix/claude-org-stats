from collections import Counter

from src.models import OrgStats, RepoFeatures


class TestRepoFeatures:
    def test_has_mcp_servers_property(self):
        repo = RepoFeatures(name="test")
        assert repo.has_mcp_servers is False

        repo.mcp_servers.append("filesystem")
        assert repo.has_mcp_servers is True


class TestOrgStatsAggregate:
    def test_aggregate_empty_repos(self):
        stats = OrgStats.aggregate("test-org", [])
        assert stats.org_name == "test-org"
        assert stats.total_repos == 0
        assert stats.repos == []
        assert stats.claude_md_count == 0
        assert stats.claude_dir_count == 0
        assert stats.mcp_servers_count == 0
        assert stats.custom_commands_count == 0
        assert stats.claude_actions_count == 0
        assert stats.hooks_count == 0
        assert stats.agents_count == 0
        assert stats.memory_count == 0
        assert stats.mcp_server_counter == Counter()
        assert stats.custom_command_counter == Counter()
        assert stats.claude_action_counter == Counter()
        assert stats.hook_type_counter == Counter()

    def test_aggregate_counts_features_correctly(self):
        repos = [
            RepoFeatures(name="repo1", has_claude_md=True, has_claude_dir=True),
            RepoFeatures(name="repo2", has_claude_md=True, has_memory=True),
            RepoFeatures(name="repo3", has_agents=True),
            RepoFeatures(name="repo4"),
        ]
        stats = OrgStats.aggregate("test-org", repos)

        assert stats.total_repos == 4
        assert stats.claude_md_count == 2
        assert stats.claude_dir_count == 1
        assert stats.memory_count == 1
        assert stats.agents_count == 1
        assert stats.mcp_servers_count == 0
        assert stats.custom_commands_count == 0
        assert stats.claude_actions_count == 0
        assert stats.hooks_count == 0

    def test_aggregate_counts_mcp_servers(self):
        repos = [
            RepoFeatures(name="repo1", mcp_servers=["filesystem", "github"]),
            RepoFeatures(name="repo2", mcp_servers=["filesystem", "slack"]),
            RepoFeatures(name="repo3", mcp_servers=[]),
        ]
        stats = OrgStats.aggregate("test-org", repos)

        assert stats.mcp_servers_count == 2  # Only repos with servers
        assert stats.mcp_server_counter["filesystem"] == 2
        assert stats.mcp_server_counter["github"] == 1
        assert stats.mcp_server_counter["slack"] == 1

    def test_aggregate_counts_custom_commands(self):
        repos = [
            RepoFeatures(
                name="repo1",
                has_custom_commands=True,
                custom_commands=["review", "test"],
            ),
            RepoFeatures(
                name="repo2",
                has_custom_commands=True,
                custom_commands=["review", "deploy"],
            ),
        ]
        stats = OrgStats.aggregate("test-org", repos)

        assert stats.custom_commands_count == 2
        assert stats.custom_command_counter["review"] == 2
        assert stats.custom_command_counter["test"] == 1
        assert stats.custom_command_counter["deploy"] == 1

    def test_aggregate_counts_claude_actions(self):
        repos = [
            RepoFeatures(
                name="repo1",
                has_claude_actions=True,
                claude_action_names=["claude-code-action"],
            ),
            RepoFeatures(
                name="repo2",
                has_claude_actions=True,
                claude_action_names=["claude-code-action", "claude-code-base-action"],
            ),
        ]
        stats = OrgStats.aggregate("test-org", repos)

        assert stats.claude_actions_count == 2
        assert stats.claude_action_counter["claude-code-action"] == 2
        assert stats.claude_action_counter["claude-code-base-action"] == 1

    def test_aggregate_counts_hooks(self):
        repos = [
            RepoFeatures(
                name="repo1",
                has_hooks=True,
                hook_types=["PreToolUse", "PostToolUse"],
            ),
            RepoFeatures(
                name="repo2",
                has_hooks=True,
                hook_types=["PreToolUse"],
            ),
        ]
        stats = OrgStats.aggregate("test-org", repos)

        assert stats.hooks_count == 2
        assert stats.hook_type_counter["PreToolUse"] == 2
        assert stats.hook_type_counter["PostToolUse"] == 1

    def test_aggregate_preserves_repos_list(self):
        repos = [
            RepoFeatures(name="repo1", has_claude_md=True),
            RepoFeatures(name="repo2", has_claude_dir=True),
        ]
        stats = OrgStats.aggregate("test-org", repos)

        assert stats.repos == repos
        assert len(stats.repos) == 2
        assert stats.repos[0].name == "repo1"
        assert stats.repos[1].name == "repo2"

    def test_aggregate_all_features_at_once(self):
        """Test a complex scenario with all feature types."""
        repos = [
            RepoFeatures(
                name="full-featured-repo",
                has_claude_md=True,
                has_claude_dir=True,
                has_custom_commands=True,
                has_claude_actions=True,
                has_hooks=True,
                has_agents=True,
                has_memory=True,
                mcp_servers=["filesystem", "github"],
                custom_commands=["review"],
                claude_action_names=["claude-code-action"],
                hook_types=["PreToolUse"],
            ),
        ]
        stats = OrgStats.aggregate("test-org", repos)

        assert stats.total_repos == 1
        assert stats.claude_md_count == 1
        assert stats.claude_dir_count == 1
        assert stats.mcp_servers_count == 1
        assert stats.custom_commands_count == 1
        assert stats.claude_actions_count == 1
        assert stats.hooks_count == 1
        assert stats.agents_count == 1
        assert stats.memory_count == 1
        assert len(stats.mcp_server_counter) == 2
        assert len(stats.custom_command_counter) == 1
        assert len(stats.claude_action_counter) == 1
        assert len(stats.hook_type_counter) == 1

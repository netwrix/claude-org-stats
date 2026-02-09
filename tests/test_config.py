import os

import pytest

from src.config import Config


class TestConfigFromEnv:
    def test_from_env_required_fields(self, monkeypatch):
        monkeypatch.setenv("INPUT_GH_TOKEN", "test-token")
        monkeypatch.setenv("INPUT_ORG_NAME", "test-org")

        config = Config.from_env()

        assert config.gh_token == "test-token"
        assert config.org_name == "test-org"

    def test_from_env_defaults(self, monkeypatch):
        monkeypatch.setenv("INPUT_GH_TOKEN", "test-token")
        monkeypatch.setenv("INPUT_ORG_NAME", "test-org")

        config = Config.from_env()

        assert config.repository == ""
        assert config.show_sections == ["adoption", "skills", "agents", "hooks", "actions"]
        assert config.blocks == "░█"
        assert config.bar_length == 25
        assert config.bar_sections == ["adoption", "skills", "agents", "hooks", "actions"]
        assert config.max_items == 10
        assert config.exclude_archived is True
        assert config.exclude_forks is True
        assert config.exclude_repos == []
        assert config.section_name == "claude-stats"
        assert config.target_path == "README.md"
        assert config.target_branch == ""
        assert config.commit_message == "Update Claude Code adoption stats"
        assert config.committer_name == "github-actions[bot]"
        assert config.committer_email == "github-actions[bot]@users.noreply.github.com"

    def test_from_env_custom_values(self, monkeypatch):
        monkeypatch.setenv("INPUT_GH_TOKEN", "custom-token")
        monkeypatch.setenv("INPUT_ORG_NAME", "custom-org")
        monkeypatch.setenv("INPUT_REPOSITORY", "org/repo")
        monkeypatch.setenv("INPUT_SHOW_SECTIONS", "adoption,details")
        monkeypatch.setenv("INPUT_BLOCKS", "⬜⬛")
        monkeypatch.setenv("INPUT_BAR_LENGTH", "50")
        monkeypatch.setenv("INPUT_BAR_SECTIONS", "adoption")
        monkeypatch.setenv("INPUT_MAX_ITEMS", "5")
        monkeypatch.setenv("INPUT_EXCLUDE_ARCHIVED", "false")
        monkeypatch.setenv("INPUT_EXCLUDE_FORKS", "false")
        monkeypatch.setenv("INPUT_EXCLUDE_REPOS", "repo1,repo2,repo3")
        monkeypatch.setenv("INPUT_SECTION_NAME", "my-stats")
        monkeypatch.setenv("INPUT_TARGET_PATH", "docs/README.md")
        monkeypatch.setenv("INPUT_TARGET_BRANCH", "main")
        monkeypatch.setenv("INPUT_COMMIT_MESSAGE", "Custom commit message")
        monkeypatch.setenv("INPUT_COMMITTER_NAME", "custom-bot")
        monkeypatch.setenv("INPUT_COMMITTER_EMAIL", "custom@example.com")

        config = Config.from_env()

        assert config.gh_token == "custom-token"
        assert config.org_name == "custom-org"
        assert config.repository == "org/repo"
        assert config.show_sections == ["adoption", "details"]
        assert config.blocks == "⬜⬛"
        assert config.bar_length == 50
        assert config.bar_sections == ["adoption"]
        assert config.max_items == 5
        assert config.exclude_archived is False
        assert config.exclude_forks is False
        assert config.exclude_repos == ["repo1", "repo2", "repo3"]
        assert config.section_name == "my-stats"
        assert config.target_path == "docs/README.md"
        assert config.target_branch == "main"
        assert config.commit_message == "Custom commit message"
        assert config.committer_name == "custom-bot"
        assert config.committer_email == "custom@example.com"

    def test_from_env_fallback_to_non_input_prefix(self, monkeypatch):
        """Test that env vars without INPUT_ prefix are used as fallback."""
        monkeypatch.setenv("GH_TOKEN", "fallback-token")
        monkeypatch.setenv("ORG_NAME", "fallback-org")

        config = Config.from_env()

        assert config.gh_token == "fallback-token"
        assert config.org_name == "fallback-org"

    def test_from_env_input_prefix_takes_precedence(self, monkeypatch):
        """Test that INPUT_ prefix takes precedence over non-prefixed."""
        monkeypatch.setenv("GH_TOKEN", "fallback-token")
        monkeypatch.setenv("INPUT_GH_TOKEN", "preferred-token")
        monkeypatch.setenv("ORG_NAME", "fallback-org")
        monkeypatch.setenv("INPUT_ORG_NAME", "preferred-org")

        config = Config.from_env()

        assert config.gh_token == "preferred-token"
        assert config.org_name == "preferred-org"

    def test_from_env_comma_list_parsing_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("INPUT_GH_TOKEN", "token")
        monkeypatch.setenv("INPUT_ORG_NAME", "org")
        monkeypatch.setenv("INPUT_SHOW_SECTIONS", "adoption , mcp , details ")
        monkeypatch.setenv("INPUT_EXCLUDE_REPOS", " repo1 , repo2 , repo3 ")
        monkeypatch.setenv("INPUT_BAR_SECTIONS", " adoption, mcp ")

        config = Config.from_env()

        assert config.show_sections == ["adoption", "mcp", "details"]
        assert config.exclude_repos == ["repo1", "repo2", "repo3"]
        assert config.bar_sections == ["adoption", "mcp"]

    def test_from_env_empty_list_values(self, monkeypatch):
        monkeypatch.setenv("INPUT_GH_TOKEN", "token")
        monkeypatch.setenv("INPUT_ORG_NAME", "org")
        monkeypatch.setenv("INPUT_SHOW_SECTIONS", "")
        monkeypatch.setenv("INPUT_EXCLUDE_REPOS", "")
        monkeypatch.setenv("INPUT_BAR_SECTIONS", "")

        config = Config.from_env()

        assert config.show_sections == []
        assert config.exclude_repos == []
        assert config.bar_sections == []

    def test_from_env_boolean_parsing(self, monkeypatch):
        monkeypatch.setenv("INPUT_GH_TOKEN", "token")
        monkeypatch.setenv("INPUT_ORG_NAME", "org")

        # Test "true" values (case insensitive)
        monkeypatch.setenv("INPUT_EXCLUDE_ARCHIVED", "true")
        monkeypatch.setenv("INPUT_EXCLUDE_FORKS", "TRUE")
        config = Config.from_env()
        assert config.exclude_archived is True
        assert config.exclude_forks is True

        # Test "false" values
        monkeypatch.setenv("INPUT_EXCLUDE_ARCHIVED", "false")
        monkeypatch.setenv("INPUT_EXCLUDE_FORKS", "FALSE")
        config = Config.from_env()
        assert config.exclude_archived is False
        assert config.exclude_forks is False

        # Test non-true values default to False
        monkeypatch.setenv("INPUT_EXCLUDE_ARCHIVED", "yes")
        monkeypatch.setenv("INPUT_EXCLUDE_FORKS", "1")
        config = Config.from_env()
        assert config.exclude_archived is False
        assert config.exclude_forks is False

    def test_from_env_integer_parsing(self, monkeypatch):
        monkeypatch.setenv("INPUT_GH_TOKEN", "token")
        monkeypatch.setenv("INPUT_ORG_NAME", "org")
        monkeypatch.setenv("INPUT_BAR_LENGTH", "100")
        monkeypatch.setenv("INPUT_MAX_ITEMS", "20")

        config = Config.from_env()

        assert config.bar_length == 100
        assert config.max_items == 20
        assert isinstance(config.bar_length, int)
        assert isinstance(config.max_items, int)

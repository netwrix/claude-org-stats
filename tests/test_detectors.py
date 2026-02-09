import json
from pathlib import Path

from src.detectors import (
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
from src.models import RepoFeatures

FIXTURES = Path(__file__).parent / "fixtures"


def _tree_paths_from_fixture() -> set[str]:
    data = json.loads((FIXTURES / "sample_tree.json").read_text())
    return {item["path"] for item in data}


class TestTreeDetectors:
    def test_detect_claude_md(self):
        features = RepoFeatures(name="test")
        detect_claude_md({"CLAUDE.md", "src/main.py"}, features)
        assert features.has_claude_md is True

    def test_detect_claude_md_nested(self):
        features = RepoFeatures(name="test")
        detect_claude_md({"packages/core/CLAUDE.md", "src/main.py"}, features)
        assert features.has_claude_md is True

    def test_detect_claude_md_missing(self):
        features = RepoFeatures(name="test")
        detect_claude_md({"README.md", "src/main.py"}, features)
        assert features.has_claude_md is False

    def test_detect_claude_dir(self):
        features = RepoFeatures(name="test")
        detect_claude_dir({".claude/settings.json", "src/main.py"}, features)
        assert features.has_claude_dir is True

    def test_detect_claude_dir_missing(self):
        features = RepoFeatures(name="test")
        detect_claude_dir({"src/main.py"}, features)
        assert features.has_claude_dir is False

    def test_detect_custom_commands(self):
        features = RepoFeatures(name="test")
        detect_custom_commands({".claude/commands/review.md", ".claude/commands/test.md"}, features)
        assert features.has_custom_commands is True
        assert sorted(features.custom_commands) == ["review", "test"]

    def test_detect_custom_commands_empty(self):
        features = RepoFeatures(name="test")
        detect_custom_commands({"src/main.py"}, features)
        assert features.has_custom_commands is False

    def test_detect_memory(self):
        features = RepoFeatures(name="test")
        detect_memory({"MEMORY.md"}, features)
        assert features.has_memory is True

    def test_detect_memory_missing(self):
        features = RepoFeatures(name="test")
        detect_memory({"README.md"}, features)
        assert features.has_memory is False

    def test_detect_agents_md_not_detected(self):
        features = RepoFeatures(name="test")
        detect_agents({"docs/AGENTS.md"}, features)
        assert features.has_agents is False

    def test_detect_agents_dir(self):
        features = RepoFeatures(name="test")
        detect_agents({".claude/agents/reviewer.md"}, features)
        assert features.has_agents is True

    def test_detect_agents_missing(self):
        features = RepoFeatures(name="test")
        detect_agents({"src/main.py"}, features)
        assert features.has_agents is False


class TestPathsNeedingContent:
    def test_identifies_content_paths(self):
        tree_paths = _tree_paths_from_fixture()
        needed = paths_needing_content(tree_paths)
        assert ".mcp.json" in needed["mcp_json"]
        assert ".claude/settings.json" in needed["settings_json"]
        assert ".github/workflows/ci.yml" in needed["workflows"]
        assert ".github/workflows/claude.yml" in needed["workflows"]

    def test_empty_tree(self):
        needed = paths_needing_content(set())
        assert needed == {"mcp_json": [], "settings_json": [], "workflows": []}


class TestContentParsers:
    def test_parse_mcp_json(self):
        content = (FIXTURES / "sample_mcp.json").read_text()
        features = RepoFeatures(name="test")
        parse_mcp_json_content(content, features)
        assert sorted(features.mcp_servers) == ["filesystem", "github", "slack"]

    def test_parse_mcp_json_invalid(self):
        features = RepoFeatures(name="test")
        parse_mcp_json_content("not json", features)
        assert features.mcp_servers == []

    def test_parse_settings_json(self):
        content = (FIXTURES / "sample_settings.json").read_text()
        features = RepoFeatures(name="test")
        parse_settings_json_content(content, features)
        assert "postgres" in features.mcp_servers
        assert features.has_hooks is True
        assert "PreToolUse" in features.hook_types
        assert "PostToolUse" in features.hook_types

    def test_parse_settings_json_no_hooks(self):
        content = json.dumps({"mcpServers": {"test": {}}})
        features = RepoFeatures(name="test")
        parse_settings_json_content(content, features)
        assert features.has_hooks is False
        assert features.mcp_servers == ["test"]

    def test_parse_workflow_claude_action(self):
        content = """
name: Claude Code Review
on: pull_request
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
"""
        features = RepoFeatures(name="test")
        parse_workflow_content(content, features)
        assert features.has_claude_actions is True
        assert "claude-code-action" in features.claude_action_names

    def test_parse_workflow_no_claude(self):
        content = """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
        features = RepoFeatures(name="test")
        parse_workflow_content(content, features)
        assert features.has_claude_actions is False

    def test_full_fixture_tree(self):
        """Test all detectors against the full fixture tree."""
        tree_paths = _tree_paths_from_fixture()
        features = RepoFeatures(name="full-test")

        detect_claude_md(tree_paths, features)
        detect_claude_dir(tree_paths, features)
        detect_custom_commands(tree_paths, features)
        detect_memory(tree_paths, features)
        detect_agents(tree_paths, features)

        assert features.has_claude_md is True
        assert features.has_claude_dir is True
        assert features.has_custom_commands is True
        assert features.has_memory is True
        assert features.has_agents is True
        assert sorted(features.custom_commands) == ["review", "test"]

# Claude Org Stats

A GitHub Action that scans repositories in your GitHub organization (or profile) and generates visual ASCII bar charts showing Claude Code adoption statistics. Great for organizations that are looking to drive Claude Code adoption and want a first-line visibility into where it is being used. Inspired by [waka-readme](https://github.com/athul/waka-readme).

## Example Output

```
📊 Claude Code Adoption (100 repos scanned)

Has CLAUDE.md          25 repos   ██████░░░░░░░░░░░░░░░░░░░  25.00 %
Has .claude/ Dir       18 repos   ████░░░░░░░░░░░░░░░░░░░░░  18.00 %
Has Skills              8 repos   ██░░░░░░░░░░░░░░░░░░░░░░░   8.00 %
Has Agents              5 repos   █░░░░░░░░░░░░░░░░░░░░░░░░   5.00 %
Has Hooks               4 repos   █░░░░░░░░░░░░░░░░░░░░░░░░   4.00 %
Has GitHub Actions      6 repos   █░░░░░░░░░░░░░░░░░░░░░░░░   6.00 %

⚡ Top Skills (of 8 repos)
review                  5 repos
commit                  3 repos
deploy                  2 repos

🕵️ Top Agents (of 5 repos)
code-reviewer           3 repos
test-writer             2 repos

🪝 Top Hooks (of 4 repos)
PreToolUse              3 repos
PostToolUse             2 repos

🤖 Top GitHub Actions (of 6 repos)
claude-code-action      5 repos
claude-code (ref)       3 repos
```

<details>
<summary>Per-repo breakdown</summary>

| Repo | CLAUDE.md | .claude/ | MCP | Skills | Actions | Hooks | Agents | Memory |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| api-service | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| frontend-app | ✅ | ✅ |  | ✅ |  |  |  |  |
| infra-tools | ✅ |  |  |  | ✅ |  |  |  |

</details>

## Setup

### 1. Add section markers to your README

Add these comments wherever you want the stats to appear:

```markdown
<!--START_SECTION:claude-stats-->
<!--END_SECTION:claude-stats-->
```

### 2. Create a workflow

Create `.github/workflows/claude-stats.yml`:

```yaml
name: Claude Code Stats

on:
  schedule:
    - cron: "0 0 * * *"  # Daily at midnight
  workflow_dispatch:       # Manual trigger

jobs:
  update-stats:
    runs-on: ubuntu-latest
    steps:
      - uses: netwrix/claude-org-stats@main
        with:
          GH_TOKEN: ${{ secrets.ORG_READ_TOKEN }}
          ORG_NAME: your-org
          REPOSITORY: ${{ github.repository }}
          SHOW_SECTIONS: "adoption,mcp,skills,actions,hooks,agents,details"
```

### 3. Create a GitHub token

Create a [Personal Access Token](https://github.com/settings/tokens) (classic) with `repo` and `read:org` scopes, or a fine-grained token with read access to organization repos. Add it as a repository secret named `ORG_READ_TOKEN`.

## What It Detects

For each repository in the organization:

| Feature | What's scanned |
|---------|---------------|
| **CLAUDE.md** | `CLAUDE.md` files at root or nested in directories |
| **.claude/ directory** | Presence of `.claude/` configuration directory |
| **MCP servers** | Server names from `.mcp.json` and `.claude/settings.json` |
| **Skills** | Files in `.claude/commands/` and `.claude/skills/` directories |
| **Claude GitHub Actions** | References to Claude actions in `.github/workflows/*.yml` |
| **Hooks** | Hook definitions in `.claude/settings.json` |
| **Agents** | Agent files in `.claude/agents/` directory |
| **Memory** | `MEMORY.md` files |

## Configuration

| Input | Default | Description |
|-------|---------|-------------|
| `GH_TOKEN` | *required* | GitHub token with org:read scope |
| `ORG_NAME` | *required* | GitHub organization to scan |
| `REPOSITORY` | `""` | Repository to update (owner/repo format) |
| `SHOW_SECTIONS` | `adoption,skills,agents,hooks,actions` | Sections to render (see below) |
| `BLOCKS` | `░█` | Bar chart characters |
| `BAR_LENGTH` | `25` | Bar width in characters |
| `BAR_SECTIONS` | `adoption,skills,agents,hooks,actions` | Sections that show progress bars (others show counts only) |
| `MAX_ITEMS` | `10` | Max items in ranked lists |
| `EXCLUDE_ARCHIVED` | `true` | Skip archived repos |
| `EXCLUDE_FORKS` | `true` | Skip forked repos |
| `EXCLUDE_REPOS` | `""` | Comma-separated repo names to skip |
| `SECTION_NAME` | `claude-stats` | Comment marker name |
| `TARGET_PATH` | `README.md` | File to update |
| `TARGET_BRANCH` | `""` | Branch to commit to (default: repo default) |
| `COMMIT_MESSAGE` | `Update Claude Code adoption stats` | Commit message |

### Custom Bar Styles

```yaml
# Default
BLOCKS: "░█"

# Gradient
BLOCKS: "░▒▓█"

# Braille
BLOCKS: "⣀⣄⣤⣦⣶⣷⣿"
```

## Local Testing

```bash
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run against a real org
export INPUT_GH_TOKEN="ghp_..."
export INPUT_ORG_NAME="your-org"
export INPUT_REPOSITORY="your-org/your-repo"
python -m src.main
```

## License

MIT

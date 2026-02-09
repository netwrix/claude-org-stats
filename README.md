# claude-org-stats

A GitHub Action that scans repositories in your GitHub organization (or profile) and generates visual ASCII bar charts showing Claude Code adoption statistics. Inspired by [waka-readme](https://github.com/athul/waka-readme).

## Example Output

```
📊 Claude Code Adoption (31 repos scanned)

Has CLAUDE.md         15 repos   ████████████░░░░░░░░░░░░░  48.39 %
Has .claude/ Dir      12 repos   ██████████░░░░░░░░░░░░░░░  38.71 %
Has MCP Servers       12 repos   ██████████░░░░░░░░░░░░░░░  38.71 %
Has Custom Commands    8 repos   ██████░░░░░░░░░░░░░░░░░░░  25.81 %
Has Claude Actions     6 repos   █████░░░░░░░░░░░░░░░░░░░░  19.35 %
Has Hooks              4 repos   ███░░░░░░░░░░░░░░░░░░░░░░  12.90 %

🔧 Top MCP Servers (of 12 repos with MCP)
filesystem            8 repos
github                6 repos
slack                 3 repos
```

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
      - uses: your-org/claude-org-stats@main
        with:
          GH_TOKEN: ${{ secrets.ORG_READ_TOKEN }}
          ORG_NAME: your-org
          REPOSITORY: ${{ github.repository }}
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
| **Custom commands** | Files in `.claude/commands/` directory |
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
| `SHOW_SECTIONS` | `adoption,mcp` | Sections to render (see below) |
| `BLOCKS` | `░█` | Bar chart characters |
| `BAR_LENGTH` | `25` | Bar width in characters |
| `BAR_SECTIONS` | `adoption,mcp,skills,actions,hooks` | Sections that show progress bars (others show counts only) |
| `MAX_ITEMS` | `10` | Max items in ranked lists |
| `EXCLUDE_ARCHIVED` | `true` | Skip archived repos |
| `EXCLUDE_FORKS` | `true` | Skip forked repos |
| `EXCLUDE_REPOS` | `""` | Comma-separated repo names to skip |
| `SECTION_NAME` | `claude-stats` | Comment marker name |
| `TARGET_PATH` | `README.md` | File to update |
| `TARGET_BRANCH` | `""` | Branch to commit to (default: repo default) |
| `COMMIT_MESSAGE` | `Update Claude Code adoption stats` | Commit message |

### Available Sections

- `adoption` - Overview bar chart of all feature adoption rates
- `mcp` - Ranked list of most common MCP servers
- `skills` - Ranked list of custom commands
- `actions` - Ranked list of Claude GitHub Actions
- `hooks` - Ranked list of hook types
- `details` - Per-repo table with checkmarks

Example with all sections:

```yaml
SHOW_SECTIONS: "adoption,mcp,skills,actions,hooks,details"
```

### Custom Bar Styles

```yaml
# Default
BLOCKS: "░█"

# Gradient
BLOCKS: "░▒▓█"

# Braille
BLOCKS: "⣀⣄⣤⣦⣶⣷⣿"
```

## API Efficiency

Uses the Git Tree API for minimal API calls:

- 1 API call per repo to get the full file tree
- 0-3 additional calls per repo only for files needing content parsing (`.mcp.json`, `.claude/settings.json`, workflow files)
- For a 100-repo org: ~100-400 API calls total, well within GitHub's 5,000/hour limit
- Rate limit detection with automatic backoff

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

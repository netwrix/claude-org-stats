# Test Suite Memory

## Project Testing Framework
- Uses pytest with 90 tests total (as of 2026-02-09)
- Test files: `test_config.py`, `test_detectors.py`, `test_graph.py`, `test_models.py`, `test_renderer.py`
- Configuration: Located in `pyproject.toml`
- Fixtures: Located in `tests/fixtures/` directory

## Key Test Patterns

### Agent Detection Tests
- **CRITICAL**: Agents are ONLY detected in `.claude/agents/` directory
- Standalone `AGENTS.md` files anywhere else do NOT trigger detection
- Test: `test_detect_agents_md_not_detected()` validates this correctly
- Test: `test_detect_agents_dir()` validates proper detection in `.claude/agents/`
- Fixture `sample_tree.json` includes both valid (`.claude/agents/reviewer.md`) and invalid (`docs/AGENTS.md`) paths

### Config Testing
- `target_path` field defaults to `"README.md"` (tested in `test_from_env_defaults`)
- Config reads from environment variables with `INPUT_` prefix or fallback to unprefixed
- All config fields have comprehensive test coverage

### Section Replacement Testing
- `_replace_section()` function in `src/main.py` has full coverage in `TestReplaceSection` class
- Tests cover: basic replacement, missing markers, custom section names, multiline content
- Function lives in `main.py` but is tested in `test_renderer.py`

## Recent Code Changes Verified (2026-02-09)
1. ✅ Agents detection only checks `.claude/agents/` - tests are correct
2. ✅ Config `target_path` field - properly tested with default value
3. ✅ `_replace_section()` - adequate test coverage exists
4. ✅ No stale tests found - all 90 tests passing

## Test Organization Notes
- Tree path detectors use fixture in `tests/fixtures/sample_tree.json`
- Content parsers use fixtures: `sample_mcp.json`, `sample_settings.json`
- Helper functions like `_make_config()` and `_make_stats()` used in renderer tests

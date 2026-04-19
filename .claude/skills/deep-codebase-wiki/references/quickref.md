# Deep Codebase Wiki - Quick Reference

## Start Here

Run this command before any repository analysis:

```bash
# For GitHub repos
bash scripts/search_wikis.sh --repo "owner/repo"

# For local directories
bash scripts/search_wikis.sh --local "/path/to/project"
```

If a wiki exists, read it first. If not, continue with Analyze Mode.

## Common Commands

```bash
# List all indexed wikis (shows source type: github/local)
bash scripts/search_wikis.sh --list

# Find a wiki by repository name
bash scripts/search_wikis.sh --repo "facebook/react"

# Find a wiki by local source path
bash scripts/search_wikis.sh --local "/Users/dev/my-project"

# Search indexed metadata (repository/name/path)
bash scripts/search_wikis.sh --query "authentication"

# Clone a GitHub repository for analysis
bash scripts/clone_repo.sh "owner/repo" --depth 1

# Prepare a local codebase for analysis (detects language, git info, etc.)
bash scripts/analyze_local.sh /path/to/project --name my-project

# Validate wiki structure and required metadata
bash scripts/validate_wiki.sh ~/.claude/wikis/org-repo

# Check whether an existing wiki should be refreshed (works for both github and local)
bash scripts/update_check.sh ~/.claude/wikis/org-repo

# Start local web reader for a wiki
bash scripts/serve_wiki_web.sh org-repo --open

# Build a static site for sharing or publishing
bash scripts/build_wiki_site.sh org-repo --out-dir ./site-org-repo

# Optional: generate codemap JSON snapshots to accelerate analysis
bash scripts/codemap_snapshot.sh /path/to/repo --ref main

# Show codemap installation status and user preference
bash scripts/codemap_status.sh --json

# Set codemap preference: ask | always | never
bash scripts/codemap_preference.sh set ask

# Install codemap after explicit user approval
bash scripts/codemap_install.sh --method auto --yes

# Register a wiki in the index (GitHub source)
bash scripts/search_wikis.sh --add "org-repo" "owner/repo" "/path/to/wiki" "commit-sha"

# Register a wiki in the index (local source)
bash scripts/search_wikis.sh --add "local-myproj" "local" "/path/to/wiki" "sha-or-none" \
  --source-type local --source-path "/original/project/path"

# Remove a wiki (deletes index entry and wiki directory)
bash scripts/search_wikis.sh --remove "org-repo"

# Run shell syntax checks for all scripts
bash scripts/check_scripts.sh
```

## Mode Selection

| Scenario | Recommended Mode | Primary Command |
|----------|------------------|-----------------|
| User asks about a known repository | **Read** | `search_wikis.sh --repo` |
| User asks about a local codebase | **Read** | `search_wikis.sh --local` |
| No wiki exists for a GitHub repo | **Analyze (GitHub)** | Clone -> Analyze -> Save |
| No wiki exists for local code | **Analyze (Local)** | `analyze_local.sh` -> Analyze -> Save |
| Wiki is old or likely stale | **Update** | `update_check.sh` -> Re-analyze |
| Multiple repositories are mentioned | **Read** | `search_wikis.sh --list` |

## Priority Order

1. Check local wiki coverage first (`deep-codebase-wiki`).
2. If no local wiki exists, use guided analysis.
3. Use manual/external exploration only as a fallback.

## Important Paths

- **Wikis root (project-local, preferred)**: `<project-root>/.claude/wikis/<wiki-name>/`
- **Wikis root (global fallback)**: `~/.claude/wikis/<wiki-name>/`
- **Wiki index (project-local)**: `<project-root>/.claude/wikis/index.json`
- **Wiki index (global)**: `~/.claude/wikis/index.json`
- **Skill location**: `~/.claude/skills/deep-codebase-wiki/`
- **Default clone temp**: `/tmp/wiki-analysis/<org>-<repo>/`

Local-source wikis are saved to the project-local index when inside a git repo. GitHub-source wikis go to the global index. Searches always check project-local first.

## Analysis Depth

| Depth | Typical Duration | Best For |
|-------|------------------|----------|
| **Quick** | 1-2 hours | Small repos and time-boxed requests |
| **Standard** | 3-5 hours | Default choice for most repos |
| **Comprehensive** | 5-8 hours | Critical systems and deep onboarding |

## Dependencies

- `bash` - script execution
- `jq` - JSON index processing (`brew install jq`)
- `git` - repository cloning/fetching (optional for non-git local analysis)
- `mkdocs` - local web reading and static site build (`pip install mkdocs`)
- `codemap` (optional) - architecture context snapshots (`brew tap JordanCoin/tap && brew install codemap`)
- `ast-grep` (optional) - required by codemap dependency mode (`brew install ast-grep`)

## Environment Overrides

- `WIKIS_DIR` - wiki data root (default: `~/.claude/wikis`)
- `INDEX_FILE` - index file path (default: `$WIKIS_DIR/index.json`)
- `WIKI_TMP_DIR` - clone temp directory (default: `/tmp/wiki-analysis`)
- `WIKI_UPDATE_TMP_DIR` - update-check temp directory (default: `/tmp/wiki-update-check`)
- `WIKI_DEFAULT_BRANCH` - default branch for clone/update scripts (default: `main`)
- `WIKI_DEFAULT_DEPTH` - default clone depth (default: `1`)
- `GIT_BASE_URL` - git host base URL (default: `https://github.com`)
- `WIKI_WEB_TMP_DIR` - MkDocs staging directory (default: `/tmp/wiki-web`)
- `WIKI_WEB_PORT` - default web port (default: `8000`)
- `WIKI_WEB_HOST` - default web host (default: `127.0.0.1`)
- `WIKI_CODEMAP_OUT_DIR` - default output directory for codemap snapshots
- `CODEMAP_REF` - default diff reference branch for codemap snapshots (default: `main`)
- `CODEMAP_PREF_FILE` - override codemap preference file location

## Writing Better Wikis

- Start with architecture and decision context, not file-by-file notes.
- Prefer a few high-quality traces over many shallow summaries.
- Reuse existing wiki docs aggressively to avoid repeated exploration.
- Record assumptions in `metadata.yaml` to simplify future updates.

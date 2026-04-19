---
name: deep-codebase-wiki
description: |
  MUST CHECK FIRST before DeepWiki or any external research. Local-first codebase documentation wikis.
  
  **Priority order for library/framework research**:
  1. deep-codebase-wiki (THIS) - check local wikis FIRST
  2. DeepWiki - only if no local wiki exists
  3. librarian/explore agents - only as fallback
  
  **Auto-trigger when**:
  - Any GitHub repository mentioned (org/repo format)
  - "How does X work?" about libraries/frameworks
  - Architecture, implementation, or codebase questions
  - Before cloning or analyzing any repository
  - Debugging external dependencies
  - User runs /deep-codebase-wiki (show interactive menu)
  
  **Workflow**: Run `search_wikis.sh --repo "owner/repo"` or `--local "$(pwd)"` first. If wiki exists, read it. If not, offer to analyze and create wiki.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, LSP, ASTGrep
---

# Deep Codebase Wiki

## Interactive Menu (on `/deep-codebase-wiki`)

When explicitly invoked, detect context and present options:

1. Run `pwd`, check git remote, run `search_wikis.sh --local "$(pwd)"`, check `codemap_status.sh --json`
2. Present:

```
Deep Codebase Wiki — Current: {cwd} {git info if available}
{Existing wiki: {path} ({age} ago) — if found}

  1. Analyze current directory    5. Serve wiki in browser
  2. Analyze a GitHub repo        6. Build static site
  3. Browse existing wikis        7. Remove a wiki
  4. Update a wiki

Options: depth (quick/standard/comprehensive), focus areas, codemap, web view after generation
```

---

## Proactive Check Protocol

Before any repository research or architecture analysis:

```bash
bash scripts/search_wikis.sh --repo "owner/repo"   # GitHub repos
bash scripts/search_wikis.sh --local "$(pwd)"       # Local codebases
```

**Wiki exists** → Read mode. **No wiki** → Offer to analyze.

Triggers: GitHub repo mentioned, "how does X work?", architecture questions, before launching explore agents, debugging dependencies.

---

## Decision Flowchart

```
Codebase mentioned or /deep-codebase-wiki
        ↓
  "owner/repo" → GitHub     local path/cwd → Local
        ↓                          ↓
  search --repo              search --local
        ↓                          ↓
    ┌───┴───┐              ┌───────┴───────┐
  Found   Not Found      Found         Not Found
    ↓       ↓              ↓               ↓
  READ    ANALYZE         READ           ANALYZE
  MODE    MODE            MODE           MODE
```

---

## Read Mode

```bash
WIKI_PATH=$(bash scripts/search_wikis.sh --repo "owner/repo")  # or --local
cat "$WIKI_PATH/overview.md"                                     # then relevant systems/
```

Check metadata freshness → read overview → navigate to relevant systems → follow cross-references → present findings.

## Analyze Mode

**Two source types**:
- **GitHub**: `bash scripts/clone_repo.sh "owner/repo" [--depth 1]`
- **Local**: `bash scripts/analyze_local.sh /path/to/project [--name custom]` — works on any directory (git or not)

**Confirmation prompt before analysis**:
> "I'll analyze {source}. Options:
> - **Depth**: quick (~1hr) / standard (~3hr) / comprehensive (~6hr)
> - **Focus**: {detected systems or 'all'}
> - **Codemap**: {status from codemap_status.sh}
> - **Web view**: open in browser when done?
>
> Which depth? Any focus areas?"

### Steps

1. **Check existing wiki**: `search_wikis.sh --repo` or `--local` (skip if recent)
2. **Prepare source**: clone (GitHub) or analyze_local.sh (local)
3. **Optional codemap**: `bash scripts/codemap_snapshot.sh "$REPO_DIR" --ref main`
4. **Multi-level analysis**: See `references/analysis-guide.md` for full methodology (Levels 1-4, timing, tools).
5. **Generate wiki**: Follow `references/wiki-schema.md` for structure. Use `assets/` templates.
6. **Validate & save**:
   ```bash
   bash scripts/validate_wiki.sh /path/to/wiki
   # GitHub → global index; Local → project-local index (when in git repo)
   bash scripts/search_wikis.sh --add "<name>" "owner/repo" "/path" "<sha>" [--source-type local --source-path "/orig"]
   ```
7. **Post-analysis options**:
   ```
   Wiki saved to: {path}
     1. Read now    2. Open in browser    3. Export HTML    4. Done
   ```
   Browser: `bash scripts/serve_wiki_web.sh "<name>" --open`
   Export: `bash scripts/build_wiki_site.sh "<name>" --out-dir ./site`

### Parallel Analysis with Sub-Agents

For large codebases (>500 files) or comprehensive depth, split work across parallel Agent invocations:

1. **Level 1 runs first** (sequential, 30-60 min) — produces `overview.md` with system list
2. **Spawn one Agent per system** for Level 2+ analysis. Each agent gets:
   - System name and description from Level 1
   - File scope (directories/patterns)
   - Template: `assets/system-template.md`
   - Output path: `systems/<name>.md`
3. **Merge results** after all agents complete:
   - Collect system docs, update overview cross-references
   - Run Level 4 traces sequentially (they span systems)
   - Validate with `scripts/validate_wiki.sh`

**Can parallelize**: independent system analysis (L2), independent component docs (L3).
**Cannot parallelize**: Level 1, cross-system traces (L4), final validation.
**When to use**: standard/comprehensive depth, 3+ systems. For quick depth or small repos, sequential is simpler.

### Wiki Storage

- **Local-source wikis** → `<project-root>/.claude/wikis/` (project-local index, preferred)
- **GitHub-source wikis** → `~/.claude/wikis/` (global index)
- Searches check project-local first, then global
- `WIKIS_DIR` env var overrides everything

## Update Mode

```bash
bash scripts/update_check.sh "$WIKI_PATH" [branch]
```

Returns `UP_TO_DATE`, `PARTIAL_UPDATE`, or `FULL_REANALYSIS` with reasons (age, change %, file count). Works for both GitHub and local wikis.

- **Partial**: re-analyze changed systems only, preserve unchanged sections
- **Full**: re-run Analyze Mode, preserve user annotations from old wiki

## Implementation Guidelines

See `references/analysis-guide.md` for depth control and `references/quickref.md` for commands, dependencies, and environment overrides.

**Quality**: Verify paths and line numbers. Cross-reference related systems. Record assumptions in metadata.
**Performance**: Shallow clones. Analyze local repos in place. Use parallel sub-agents for large codebases.

## Resources

See `references/quickref.md` for full command reference, dependencies, and environment overrides.
See `references/analysis-guide.md` for detailed multi-level analysis methodology.
See `references/wiki-schema.md` for wiki structure and metadata schema.
Templates: `assets/wiki-template/`, `assets/system-template.md`, `assets/component-template.md`, `assets/trace-template.md`.

## Integration Priority

1. `search_wikis.sh --repo` or `--local` first
2. If found → use local wiki immediately
3. If not found → offer Analyze Mode
4. External exploration only if analysis declined

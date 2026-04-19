# Script Smoke Tests

Use this checklist to run fast confidence checks after script changes.

## 1) Syntax Gate

```bash
bash scripts/check_scripts.sh
```

Expected result: `All script syntax checks passed.`

## 2) Index Operations

Use a disposable index directory:

```bash
TMP_ROOT="$(mktemp -d)"
command -v jq >/dev/null || { echo "Install jq first"; exit 1; }
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --list
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --add "demo-repo" "demo/repo" "/tmp/demo-repo" "0123456789abcdef0123456789abcdef01234567"
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --repo "demo/repo"
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --query "demo"
```

Verify:
- Index file is created automatically.
- `--repo` returns `/tmp/demo-repo`.
- `--query` returns the added entry.

## 2b) Remove Operation

```bash
TMP_ROOT="$(mktemp -d)"
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --add "del-test" "demo/repo" "$TMP_ROOT/wikis/del-test" "abcdef1234567890abcdef1234567890abcdef12"
mkdir -p "$TMP_ROOT/wikis/del-test"
echo "test" > "$TMP_ROOT/wikis/del-test/overview.md"
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --remove "del-test"
```

Verify:
- Index no longer contains `del-test`.
- Directory `$TMP_ROOT/wikis/del-test` no longer exists.
- Removing a non-existent wiki prints an error and exits non-zero.

## 3) Validate Wiki Script

Create a minimal valid wiki:

```bash
WIKI_DIR="$(mktemp -d)"
mkdir -p "$WIKI_DIR"/{systems,components,traces}
cat > "$WIKI_DIR/metadata.yaml" <<'EOF'
repository: demo/repo
analyzed_at: '2026-01-10T00:00:00Z'
commit_sha: 0123456789abcdef0123456789abcdef01234567
scope: full
EOF
cat > "$WIKI_DIR/overview.md" <<'EOF'
This overview intentionally contains enough text to pass the minimum length check.
It describes architecture decisions, repository boundaries, key systems, integration
paths, and quality constraints in one place. It also mentions dependency assumptions,
index behavior, storage layout, and validation expectations so the validator sees a
realistic overview document with more than fifty words and no short-overview warning.
EOF
bash scripts/validate_wiki.sh "$WIKI_DIR"
```

Expected result: validation succeeds.

Then test the failure path:

```bash
rm "$WIKI_DIR/metadata.yaml"
if bash scripts/validate_wiki.sh "$WIKI_DIR"; then
  echo "Unexpected pass"
  exit 1
fi
```

Expected result: the script exits with failure and prints `ERROR: Missing required file: metadata.yaml`.

## 3b) Validate Local Wiki

Create a minimal local-source wiki:

```bash
WIKI_DIR="$(mktemp -d)"
mkdir -p "$WIKI_DIR"/{systems,components,traces}
cat > "$WIKI_DIR/metadata.yaml" <<'EOF'
source_type: local
source_path: /tmp/my-project
analyzed_at: '2026-01-10T00:00:00Z'
scope: full
EOF
cat > "$WIKI_DIR/overview.md" <<'EOF'
This overview intentionally contains enough text to pass the minimum length check.
It describes architecture decisions, repository boundaries, key systems, integration
paths, and quality constraints in one place. It also mentions dependency assumptions,
index behavior, storage layout, and validation expectations so the validator sees a
realistic overview document with more than fifty words and no short-overview warning.
EOF
bash scripts/validate_wiki.sh "$WIKI_DIR"
```

Expected result: validation succeeds (no error about missing repository field for local wikis).

## 3c) Analyze Local Script

```bash
bash scripts/analyze_local.sh /tmp
bash scripts/analyze_local.sh /tmp --name my-test
```

Expected result:
- Outputs wiki name, source path, git status, primary language, file count.
- `--name` flag overrides the auto-derived name.

Argument validation:

```bash
if bash scripts/analyze_local.sh; then
  echo "Unexpected pass"
  exit 1
fi
```

Expected result: fails with usage message.

## 3d) Index Local Source Operations

```bash
TMP_ROOT="$(mktemp -d)"
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --add "local-demo" "local" "/tmp/demo-wiki" "none" --source-type local --source-path "/tmp/demo-project"
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --local "/tmp/demo-project"
WIKIS_DIR="$TMP_ROOT/wikis" bash scripts/search_wikis.sh --list
```

Verify:
- `--add` with `--source-type local` succeeds.
- `--local` returns `/tmp/demo-wiki`.
- `--list` shows `[local]` source type.

## 4) Clone Script Argument Handling

No network access is required for argument-parsing checks:

```bash
if bash scripts/clone_repo.sh; then
  echo "Unexpected pass"
  exit 1
fi

if bash scripts/clone_repo.sh "owner/repo" --unknown-flag; then
  echo "Unexpected pass"
  exit 1
fi
```

Expected result: both commands fail with clear usage/error messages.

## 5) Update Check Parsing and Dependencies

Create a local wiki directory without network calls:

```bash
WIKI_DIR="$(mktemp -d)"
cat > "$WIKI_DIR/metadata.yaml" <<'EOF'
repository: owner/repo
analyzed_at: '2026-01-10T00:00:00Z'
commit_sha: 0123456789abcdef0123456789abcdef01234567
scope: full
EOF
```

Run:

```bash
WIKI_UPDATE_TMP_DIR="$(pwd)/.tmp-update-check" bash scripts/update_check.sh "$WIKI_DIR" || true
```

Expected result:
- Metadata parsing works (no immediate metadata field errors).
- If clone/fetch cannot run (offline/sandbox), failure is due to git/network stage, not parsing stage.

## 6) Web Reader Scripts

Argument validation checks:

```bash
if bash scripts/serve_wiki_web.sh; then
  echo "Unexpected pass"
  exit 1
fi

if bash scripts/build_wiki_site.sh; then
  echo "Unexpected pass"
  exit 1
fi
```

Optional runtime check (requires MkDocs and an existing wiki):

```bash
if command -v mkdocs >/dev/null 2>&1; then
  bash scripts/build_wiki_site.sh org-repo --out-dir ./site-org-repo
fi
```

## 7) Optional Codemap Integration

If codemap is not installed, the script should skip gracefully:

```bash
bash scripts/codemap_snapshot.sh . || true
```

Expected result:
- Exit code is `0`.
- Output includes a warning that codemap is not installed.

If codemap is installed, run:

```bash
bash scripts/codemap_snapshot.sh . --ref main
```

Expected result:
- `.codemap-snapshot/overview.json` is generated.
- `.codemap-snapshot/diff.json` is generated.
- `.codemap-snapshot/context.json` is generated.
- `deps.json` is generated when dependency mode is available.

## 8) Codemap Preference and Install Helpers

Preference checks:

```bash
bash scripts/codemap_preference.sh get
bash scripts/codemap_preference.sh set ask
bash scripts/codemap_preference.sh get
bash scripts/codemap_preference.sh reset
```

Expected result:
- `get` returns one of `ask|always|never`.
- `set` persists the requested value.
- `reset` restores default behavior (`ask`).

Status checks:

```bash
bash scripts/codemap_status.sh
bash scripts/codemap_status.sh --json
```

Expected result:
- Script reports install state and current preference.
- JSON mode returns a parseable object.

Install safety checks:

```bash
if bash scripts/codemap_install.sh --dry-run; then
  echo "Dry run passed"
fi

if bash scripts/codemap_install.sh; then
  echo "Unexpected pass"
  exit 1
fi
```

Expected result:
- `--dry-run` prints selected install command.
- Running without `--yes` fails with an explicit confirmation error.

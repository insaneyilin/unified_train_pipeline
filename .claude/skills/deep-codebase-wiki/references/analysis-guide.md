# Deep Codebase Analysis Guide

## Analysis Philosophy

The goal is operational understanding, not documentation volume. Focus on:
- **Architecture decisions**: Why systems are structured this way
- **Data flows**: How information moves through the codebase
- **Entry points**: Where execution begins
- **Integration points**: How systems connect
- **Critical paths**: Security, performance, correctness

## Multi-Level Analysis Process

### Level 1: Repository Overview (30-60 minutes)

**Goal**: Understand repository structure, technology stack, and entry points.

**Steps**:

1. **Identify Languages and Frameworks**
   ```bash
   # Use Glob to find primary file types
   glob "**/*.{js,ts,py,go,rs,java}" --limit 100
   ```

2. **Locate Entry Points**
   - Web apps: `index.html`, `main.js`, `app.py`, `server.ts`
   - CLIs: `cli.py`, `main.go`, `cmd/`
   - Libraries: `index.ts`, `__init__.py`, `lib.rs`

3. **Map Directory Structure**
   ```bash
   # Get high-level directory structure
   tree -L 2 -d /path/to/repo
   ```

4. **Read Core Documentation**
   - README.md
   - ARCHITECTURE.md / DESIGN.md
   - CONTRIBUTING.md
   - docs/ directory

5. **Identify Dependencies**
   - package.json, requirements.txt, go.mod, Cargo.toml
   - Note major frameworks (React, Django, Express, etc.)

**Output**: Populate `overview.md` with architecture summary and tech stack.

### Level 2: System Architecture (1-3 hours)

**Goal**: Map major systems and their boundaries.

**Approach**:

1. **Identify System Boundaries**
   
   Look for natural divisions:
   - **By layer**: Frontend, Backend, Database, API
   - **By feature**: Auth, Payments, Notifications, Search
   - **By module**: User management, Content delivery, Analytics
   - **By service**: Microservices architecture

2. **Trace System Responsibilities**
   
   For each system, answer:
   - What is its purpose?
   - What data does it own?
   - What operations does it perform?
   - What does it expose to other systems?

3. **Map Inter-System Dependencies**
   
   Use tools:
   ```bash
   # Find imports/requires
   rg "import.*AuthService" --glob "*.ts"
   
   # AST-based import analysis
   ast-grep --pattern "import { $$ } from '$MODULE'"
   ```

4. **Document Configuration**
   
   Identify configuration mechanisms:
   - Environment variables (.env, .env.example)
   - Config files (config.json, settings.py)
   - Feature flags
   - Build-time vs runtime config

**Output**: Create one `systems/<name>.md` per major system.

### Level 3: Component Analysis (2-5 hours)

**Goal**: Document key components and their interactions.

**Selective Approach** - Don't document everything:
- **High impact**: Core business logic, critical paths
- **Complex**: Non-obvious algorithms, intricate state management
- **Frequently referenced**: Heavily imported/used components
- **User-requested**: Specific focus areas from analysis request

**Techniques**:

1. **Use LSP for Accurate Type Info**
   ```
   lsp_document_symbols("path/to/file.ts")
   lsp_goto_definition("path/to/file.ts", line, char)
   lsp_find_references("path/to/file.ts", line, char)
   ```

2. **Pattern Discovery with AST-grep**
   ```bash
   # Find all classes
   ast-grep --pattern "class $NAME { $$$ }" --lang typescript
   
   # Find all exported functions
   ast-grep --pattern "export function $NAME($$$) { $$$ }"
   ```

3. **Dependency Mapping**
   
   For each component, track:
   - What it imports (dependencies)
   - What imports it (dependents)
   - Circular dependencies (smell)

**Output**: Create `components/<name>.md` for significant components only.

### Level 4: Trace Flows (1-2 hours)

**Goal**: Document how common user journeys execute through the codebase.

**Identify Key Flows**:
- Authentication/authorization
- Main user actions (create post, checkout, upload file)
- Data pipelines (ingestion → processing → storage)
- Error handling and recovery
- Background jobs and scheduled tasks

**Tracing Technique**:

1. **Start at Entry Point**
   - HTTP endpoint, CLI command, event handler
   
2. **Follow Execution Path**
   - Step through function calls
   - Note state changes
   - Track data transformations
   
3. **Document Decision Points**
   - Conditionals that change flow
   - Error paths
   - Async operations
   
4. **Identify Side Effects**
   - Database writes
   - External API calls
   - File system operations
   - Message queue publishes

**Tools**:
```bash
# Find function call sites
lsp_find_references("path/to/service.ts", line, char)

# Search for specific call patterns
rg "await.*processPayment" --glob "*.ts"
```

**Output**: Create `traces/<flow-name>.md` for each critical flow.

## Analysis Depth Control

### Quick Analysis (< 1 hour)
- Level 1 only
- overview.md with basic structure
- No system/component docs
- Use when: Quick reference, small repos, time-constrained

### Standard Analysis (2-4 hours)
- Levels 1 + 2
- Complete overview.md
- Major systems documented
- Minimal component docs
- Use when: Default, medium repos, general understanding

### Comprehensive Analysis (5-10 hours)
- Levels 1 + 2 + 3 + 4
- Complete wiki with all sections
- Detailed component documentation
- Multiple flow traces
- Use when: Critical understanding needed, onboarding, large refactoring

## Tool Selection Guide

| Need | Tool | Example |
|------|------|---------|
| Find files by pattern | Glob | `glob "**/*Service.ts"` |
| Search code content | rg | `rg "authentication" --glob "*.py"` |
| Type information | LSP | `lsp_hover(file, line, char)` |
| Find definitions | LSP | `lsp_goto_definition(file, line, char)` |
| Find all usages | LSP | `lsp_find_references(file, line, char)` |
| Pattern matching | AST-grep | `ast-grep --pattern "class $X extends $Y"` |
| File hierarchy | Bash | `tree -L 3` |

## Quality Checklist

Before finalizing wiki:

- [ ] All file paths verified to exist
- [ ] Line number references current for analyzed commit
- [ ] Cross-references resolve correctly
- [ ] No broken links between documents
- [ ] metadata.yaml complete and valid
- [ ] overview.md covers all major systems
- [ ] System docs explain purpose and data flow
- [ ] At least 2-3 flow traces documented
- [ ] User's focus areas thoroughly covered
- [ ] Ran `scripts/validate_wiki.sh` with no errors

## Common Pitfalls

**Avoid**:
- Documenting every file (focus on important ones)
- Copy-pasting code without explanation (summarize intent)
- Missing inter-system relationships (connections matter)
- Outdated line numbers (verify before saving)
- Vague descriptions (be specific)
- Over-documenting obvious code (focus on non-obvious)
- Ignoring error handling (it's critical)
- Skipping configuration (causes confusion)

## Performance Optimization

**Large Repositories (>1000 files)**:
- Use shallow clone (`--depth 1`)
- Focus analysis on specific directories
- Parallelize independent system analysis
- Cache LSP results for frequently accessed files
- Use AST-grep for bulk pattern discovery

**Incremental Updates**:
- Only re-analyze changed systems
- Preserve unchanged documentation
- Update metadata with partial update timestamp
- Document what changed since last analysis

## Example Analysis Session

```
User request: "Analyze Supabase focusing on authentication"

1. Level 1 - Repository Overview (45 min)
   - Clone supabase/supabase
   - Identify: TypeScript, PostgreSQL, Go
   - Entry: apps/studio, apps/www
   - Frameworks: Next.js, React, PostgREST
   - Create overview.md

2. Level 2 - System Architecture (90 min)
   - Identify auth system boundaries:
     * GoTrue (auth server in Go)
     * Auth client library (TypeScript)
     * Auth UI components (React)
     * PostgreSQL RLS integration
   - Create systems/authentication.md
   - Create systems/database-auth.md

3. Level 3 - Component Analysis (60 min)
   - Focus on auth-related components:
     * components/auth-provider.md
     * components/session-manager.md
     * components/rls-policies.md

4. Level 4 - Flow Tracing (45 min)
   - Trace key flows:
     * traces/signup-flow.md
     * traces/magic-link-flow.md
     * traces/oauth-flow.md

5. Validation & Save (15 min)
   - Run scripts/validate_wiki.sh
   - Fix any broken references
   - Save to .claude/wikis/supabase-supabase/

Total: ~4 hours for comprehensive focused analysis
```

## Adaptive Analysis

Adjust depth based on repository characteristics:

| Repo Size | Primary Strategy | Estimated Time |
|-----------|------------------|----------------|
| < 100 files | Comprehensive | 2-3 hours |
| 100-500 files | Standard with selective components | 3-5 hours |
| 500-2000 files | Focused systems + key flows | 4-6 hours |
| > 2000 files | Scoped to user's focus areas | 5-8 hours |

**Prioritize quality over breadth.** A deep analysis of critical systems is more useful than shallow coverage of every file.

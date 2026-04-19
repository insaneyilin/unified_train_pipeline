# Wiki Schema Documentation

## Overview

This schema defines a hierarchical wiki structure optimized for codebase understanding and fast navigation.

## Directory Structure

Wikis are stored in two locations (project-local is preferred for local analysis):
- **Project-local**: `<project-root>/.claude/wikis/<wiki-name>/` (for local codebases inside a git repo)
- **Global**: `~/.claude/wikis/<wiki-name>/` (for GitHub repos or when no project root detected)

The directory name is derived from the source:
- GitHub repos: `<org>-<repo>` (e.g., `facebook-react`)
- Local projects: `local-<dirname>` or `<org>-<repo>` if a git remote exists

Each location has its own `index.json`. Searches check project-local first, then global.

```
~/.claude/wikis/<wiki-name>/
├── metadata.yaml          # Source and analysis metadata
├── overview.md            # High-level architecture summary
├── systems/               # Major system documentation
│   ├── authentication.md
│   ├── data-layer.md
│   ├── api-routing.md
│   └── ...
├── components/            # Component-level documentation
│   ├── user-model.md
│   ├── auth-service.md
│   └── ...
└── traces/                # User journey and flow traces
    ├── login-flow.md
    ├── api-request.md
    └── ...
```

## File Formats

### metadata.yaml

Required fields:
- `source_type` (string): `"github"` for cloned repos or `"local"` for local directories
- `analyzed_at` (string): ISO 8601 timestamp of analysis
- `scope` (string): Analysis scope ("full" | "focused" | "partial")
- `primary_language` (string): Main language detected
- `frameworks` (array): Detected frameworks and libraries

Conditional fields (depends on `source_type`):
- `repository` (string): Required for `github`. Format: "owner/repo"
- `commit_sha` (string): Required for `github`. Full 40-character commit SHA
- `source_path` (string): Required for `local`. Absolute path to original directory

Optional fields:
- `focus_areas` (array): Specific systems/features analyzed
- `analysis_depth` (string): Depth level ("quick" | "standard" | "comprehensive")
- `partial_update_history` (array): Previous partial update timestamps
- `user_annotations` (object): Custom user notes

Example (GitHub repo):
```yaml
source_type: github
repository: facebook/react
analyzed_at: '2026-01-10T05:00:00Z'
commit_sha: abc123def456789abc123def456789abc123def4
scope: focused
primary_language: JavaScript
frameworks:
  - React
  - Jest
  - Rollup
focus_areas:
  - reconciliation
  - hooks
  - fiber-architecture
analysis_depth: comprehensive
```

Example (local codebase):
```yaml
source_type: local
source_path: /Users/dev/my-project
analyzed_at: '2026-04-18T12:00:00Z'
commit_sha: abc123def456789abc123def456789abc123def4
scope: full
primary_language: TypeScript
frameworks:
  - Next.js
  - Prisma
analysis_depth: standard
```

### overview.md

Required sections:
1. **# Overview** - One-paragraph summary
2. **## Architecture** - System-level architecture description
3. **## Key Systems** - List of major systems with brief descriptions
4. **## Technology Stack** - Languages, frameworks, build tools
5. **## Directory Structure** - High-level directory organization
6. **## Getting Started** - Links to entry points and main files

Optional sections:
- **## Design Patterns** - Notable patterns used
- **## External Dependencies** - Critical third-party integrations
- **## Security Considerations** - Security-critical areas
- **## Performance Characteristics** - Known performance patterns

Writing guidelines:
- Start with high-level, end with specific details
- Include file paths with line number references where relevant
- Cross-reference to system docs using relative links
- Keep under 500 lines; move details to system docs

### systems/*.md

Each system document should describe one cohesive architectural subsystem.

Required sections:
1. **# System Name** - Title matching filename
2. **## Purpose** - What this system does
3. **## Components** - Key classes/modules/functions
4. **## Data Flow** - How data moves through the system
5. **## File Locations** - Where code lives

Optional sections:
- **## Configuration** - Environment variables, config files
- **## Dependencies** - Internal and external dependencies
- **## API/Interface** - Public interfaces exposed
- **## Error Handling** - How errors are managed
- **## Testing** - Test locations and coverage
- **## Security** - Security considerations specific to this system
- **## Performance** - Performance characteristics and bottlenecks

Writing guidelines:
- Use code blocks with file paths as titles
- Include line number references: `path/to/file.js:42-58`
- Cross-reference related systems
- Limit to 1000 lines per system; split if larger

Example:

```markdown
# Authentication System

## Purpose

Handles user authentication, session management, and authorization across the application.

## Components

### AuthService (`src/auth/AuthService.ts:1-120`)

Central authentication orchestrator. Manages login, logout, token refresh.

Key methods:
- `login(credentials)` - Authenticates user and creates session
- `refreshToken()` - Refreshes expired access tokens
- `logout()` - Invalidates session and clears tokens

### TokenManager (`src/auth/TokenManager.ts:1-85`)

Manages JWT token lifecycle and validation.

### SessionStore (`src/auth/SessionStore.ts:1-65`)

Persists session data in Redis with TTL.

## Data Flow

```
User Credentials
    ↓
AuthService.login()
    ↓
UserRepository.findByEmail()
    ↓
PasswordHasher.verify()
    ↓
TokenManager.generate()
    ↓
SessionStore.create()
    ↓
Access Token + Refresh Token
```

## File Locations

- Core logic: `src/auth/`
- Models: `src/models/User.ts`, `src/models/Session.ts`
- Middleware: `src/middleware/authenticate.ts`
- Tests: `tests/auth/`

## Dependencies

Internal:
- Database layer → UserRepository
- Config → JWT_SECRET, TOKEN_EXPIRY

External:
- `bcrypt` for password hashing
- `jsonwebtoken` for JWT operations
- Redis for session storage

## Security

- Passwords hashed with bcrypt (cost factor: 12)
- JWTs signed with HS256
- Refresh tokens stored with HTTP-only cookies
- Rate limiting on login endpoint (10 req/min)
- Session invalidation on password change
```

### components/*.md

Component documents describe individual classes, modules, or functions that are important to understanding the system.

Structure:
1. **# Component Name**
2. **## Responsibility** - Single responsibility
3. **## Interface** - Public API
4. **## Implementation** - Key logic
5. **## Usage Examples** - Code examples
6. **## Dependencies** - What it depends on
7. **## Tested By** - Test file locations

Keep under 300 lines per component.

### traces/*.md

Trace documents capture user journeys, data transformations, or operational flows.

Structure:
1. **# Flow Name**
2. **## Overview** - What this trace covers
3. **## Steps** - Numbered steps with file references
4. **## Sequence Diagram** - Mermaid or ASCII diagram (optional)
5. **## Error Paths** - What happens when things fail
6. **## Related Traces** - Cross-references

Example:

```markdown
# User Login Flow

## Overview

Traces the complete login process from form submission to authenticated session.

## Steps

1. **Form Submission** (`src/components/LoginForm.tsx:45-52`)
   User submits email/password, triggers `handleSubmit()`

2. **API Request** (`src/api/auth.ts:12-20`)
   POST request to `/api/auth/login` with credentials

3. **Controller Handler** (`src/controllers/AuthController.ts:28-45`)
   Validates input, calls AuthService

4. **Authentication** (`src/auth/AuthService.ts:35-60`)
   Verifies credentials, generates tokens

5. **Session Creation** (`src/auth/SessionStore.ts:22-35`)
   Persists session in Redis

6. **Response** (`src/controllers/AuthController.ts:46-52`)
   Returns tokens + user object

## Sequence Diagram

```
User → LoginForm → API Client → AuthController → AuthService → UserRepository → Database
                                                     ↓
                                            TokenManager
                                                     ↓
                                            SessionStore → Redis
```

## Error Paths

- Invalid credentials → 401 response, no session created
- Database error → 500 response, logged to error tracking
- Rate limit exceeded → 429 response, temporary lockout

## Related Traces

- [Logout Flow](logout-flow.md)
- [Token Refresh Flow](token-refresh-flow.md)
```

## Cross-Referencing

Use relative Markdown links:

From overview.md to system doc:
```markdown
See [Authentication System](systems/authentication.md) for details.
```

From system doc to component:
```markdown
The [UserRepository](../components/user-repository.md) handles database access.
```

From system to trace:
```markdown
See the [Login Flow trace](../traces/login-flow.md) for the complete process.
```

## Naming Conventions

- **Directories**: lowercase with hyphens (`api-routing`, not `API_Routing`)
- **Files**: lowercase with hyphens (`authentication.md`, not `Authentication.md`)
- **Sections**: Title Case with proper capitalization
- **Code references**: Use exact casing from source (`AuthService`, not `authservice`)

## Best Practices

1. **Accuracy**: Verify all file paths and line numbers before saving.
2. **Completeness**: Cover all major flows inside the selected scope.
3. **Clarity**: Write for engineers who are new to the codebase.
4. **Conciseness**: Be complete without unnecessary verbosity.
5. **Freshness**: Include analyzed commit SHA in code references.
6. **Navigation**: Ensure every document links to related documents.

## Size Limits

- overview.md: < 500 lines
- systems/*.md: < 1000 lines (split if larger)
- components/*.md: < 300 lines
- traces/*.md: < 400 lines

If approaching limits, split into multiple focused documents.

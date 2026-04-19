# Component Name

**Location**: `path/to/component.ts:1-100`

## Responsibility

[Describe this component's single responsibility and why it exists in the architecture.]

## Interface

**Exports**:
- `export class ClassName` - [What this class is responsible for]
- `export function functionName()` - [What this function returns or triggers]

**Public API**:
```typescript
class ClassName {
  constructor(params)
  publicMethod(): ReturnType
  anotherMethod(args): ReturnType
}
```

## Implementation

**Key Logic**:

[Summarize the core implementation choices, with emphasis on non-obvious logic.]

**State Management**:
- `internalState` - [What it tracks and when it changes]

**Algorithms**:
- [Describe any non-trivial algorithm, optimization, or ordering rule]

## Usage Examples

```typescript
import { ClassName } from './component';

const instance = new ClassName(config);
const result = instance.publicMethod();
```

## Dependencies

**Uses**:
- [Dependency 1](dependency-1.md) - [How this component depends on it]
- `external-library` - [Why this dependency is required]

**Used By**:
- [Parent Component](parent.md) - [How the parent integrates this component]
- [Another User](another.md) - [Secondary call site or usage context]

## Error Handling

[Document expected failures, fallback behavior, retries, and surfaced error types.]

## Testing

**Test File**: `tests/component.test.ts`

**Test Coverage**:
- [ ] Happy path scenarios
- [ ] Error conditions
- [ ] Edge cases

## Related Components

- [Related Component 1](related-1.md)
- [Related Component 2](related-2.md)

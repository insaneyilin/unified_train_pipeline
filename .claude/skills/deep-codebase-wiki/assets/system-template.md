# System Name

## Purpose

[Describe what this system owns, what problems it solves, and why it is separated from other systems.]

## Components

### Component Name (`path/to/component.ts:1-100`)

[Describe this component's role inside the system and key responsibilities.]

**Key Methods/Functions**:
- `methodName()` - [Primary behavior and expected inputs/outputs]
- `anotherMethod()` - [Secondary behavior or lifecycle interaction]

### Another Component (`path/to/other.ts:1-50`)

[Describe how this component collaborates with the previous one.]

## Data Flow

```
Input
  ↓
Component A
  ↓
Component B
  ↓
Output
```

[Explain how data enters, is transformed, and exits this system.]

## File Locations

- Core logic: `path/to/core/`
- Models: `path/to/models/`
- Tests: `path/to/tests/`

## Dependencies

**Internal**:
- [Other System](other-system.md) - [How this system depends on it]

**External**:
- `library-name` - [Why this dependency is required]

## Configuration

**Environment Variables**:
- `VAR_NAME` - [What it controls and expected values]

**Config Files**:
- `path/to/config.json` - [Relevant fields and their impact]

## API/Interface

[Document public interfaces, contracts, and expected caller behavior.]

## Error Handling

[Describe validation failures, retry behavior, and escalation/alerting paths.]

## Security

[List trust boundaries, auth checks, and handling of sensitive data.]

## Performance

[Capture expected throughput, latency constraints, and known bottlenecks.]

## Testing

Test files: `tests/system-name/`

Coverage: [X%] (as of [commit])

## Related Systems

- [Related System 1](related-system-1.md)
- [Related System 2](related-system-2.md)

## Related Traces

- [Flow involving this system](../traces/relevant-flow.md)

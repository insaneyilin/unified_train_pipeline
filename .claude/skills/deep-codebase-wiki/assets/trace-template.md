# Flow Name

## Overview

[Explain what this flow achieves and why it matters to users or system behavior.]

## Trigger

[Describe what starts this flow (user action, API call, scheduled task, or event).]

## Steps

### 1. Step Name (`path/to/file.ts:10-20`)

[Describe what happens in this step and why it is required.]

**Key Operations**:
- [Operation 1 and its side effect]
- [Operation 2 and its data impact]

**State Changes**:
- [What state changes and where it is persisted]

### 2. Next Step (`path/to/other.ts:45-60`)

[Describe the handoff from the previous step and any branching logic.]

**Data Transformation**:
```
Input: { ... }
  ↓
Processing
  ↓
Output: { ... }
```

### 3. Final Step (`path/to/final.ts:100-120`)

[Describe completion behavior, returned result, and observable side effects.]

## Sequence Diagram

```
Actor A → Component B: request
Component B → Component C: process
Component C → Database: query
Database → Component C: results
Component C → Component B: response
Component B → Actor A: final result
```

## Success Path

[Summarize the expected end-to-end happy path in plain language.]

## Error Paths

### Error Condition 1

**Trigger**: [What causes this error]

**Handling**:
1. [Step 1 of error handling]
2. [Step 2]

**Result**: [How the system recovers or fails]

### Error Condition 2

[Describe another realistic failure mode and how it is handled.]

## Data Flow

**Input**:
```json
{
  "field": "value"
}
```

**Output**:
```json
{
  "result": "value"
}
```

**Transformations**:
- Step 1: [How input shape changes]
- Step 2: [How output is derived]

## Side Effects

- Database write to `table_name`
- External API call to `service`
- File written to `path`
- Event published to `queue`

## Performance Characteristics

- Average duration: [X ms]
- Peak load handling: [Y req/sec]
- Bottlenecks: [Known bottlenecks and mitigation ideas]

## Security Considerations

- [Authentication and authorization checks]
- [Input validation and sanitization]
- [Sensitive data handling and redaction]

## Related Flows

- [Related Flow 1](related-flow-1.md) - [How this flow connects]
- [Related Flow 2](related-flow-2.md) - [When to read this next]

## Related Systems

- [System 1](../systems/system-1.md) - [How it participates in this flow]
- [System 2](../systems/system-2.md) - [How it participates in this flow]

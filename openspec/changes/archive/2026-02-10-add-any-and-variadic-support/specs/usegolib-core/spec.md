## ADDED Requirements

### Requirement: Support Type `any` (V0.x)
The type bridge SHALL support Go `any` (`interface{}`) as a dynamic value that can carry any MessagePack-compatible value.

Supported containers SHALL include at least:
- `[]any`
- `map[string]any`

#### Scenario: Call symbol with any parameter
- **WHEN** a callable symbol accepts an `any` parameter
- **AND WHEN** Python passes a MessagePack-compatible value
- **THEN** the call succeeds

#### Scenario: Return any result
- **WHEN** a callable symbol returns `any`
- **THEN** Python receives the dynamic value

### Requirement: Variadic Parameters (V0.x)
The builder scanner SHALL detect variadic parameters and record them as `...T` in symbol signatures.

When manifest schema is present, the runtime SHALL allow Python calls to pass variadic arguments naturally and SHALL pack them into the ABI form for encoding.

#### Scenario: Call variadic function from Python
- **WHEN** a callable symbol has a variadic parameter (`...T`)
- **AND WHEN** Python passes multiple arguments for that parameter
- **THEN** the runtime packs the arguments and the call succeeds

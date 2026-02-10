## ADDED Requirements

### Requirement: Generic Function Instantiation (V0.x)
The builder SHALL support exported top-level generic Go functions by generating concrete instantiations at build time for an explicit set of type arguments.

The manifest schema SHALL record the mapping from:
- generic function name + type arguments
- to the concrete callable symbol name exported by the bridge

The runtime SHALL provide a Python API to call a generic function instantiation by specifying the generic function name and type arguments.

#### Scenario: Build instantiates a generic function and Python calls it
- **WHEN** the builder is configured to instantiate an exported generic Go function with concrete type arguments
- **AND WHEN** Python calls that instantiation through the runtime
- **THEN** the call succeeds and returns the correct result

#### Scenario: Calling a non-configured generic instantiation fails
- **WHEN** Python requests a generic instantiation that is not present in the manifest schema
- **THEN** the runtime fails with an error


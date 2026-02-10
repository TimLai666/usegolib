## Purpose

Define the end-to-end behavior of `usegolib`: importing Go modules/packages from Python, version rules, build/load mechanics, ABI encoding, and supported cross-language types for v0.
## Requirements
### Requirement: Python Import API
The system SHALL expose a Python API that imports a Go module or subpackage and returns a handle that can be used to call exported Go identifiers.

#### Scenario: Import root module from the default artifact root
- **WHEN** Python calls `usegolib.import_("example.com/mod", version=None)`
- **THEN** the system searches the default artifact root for a matching artifact for the current OS/arch
- **AND THEN** the system loads the matching shared library into the current Python process
- **AND THEN** the call returns a handle bound to package `example.com/mod`

#### Scenario: Import root module from an explicit artifact root
- **WHEN** Python calls `usegolib.import_("example.com/mod", version=None, artifact_dir="out/")`
- **THEN** the system searches `artifact_dir` for a matching artifact for the current OS/arch
- **AND THEN** the system loads the matching shared library into the current Python process
- **AND THEN** the call returns a handle bound to package `example.com/mod`

#### Scenario: Import subpackage returns a handle bound to that package
- **WHEN** Python calls `usegolib.import_("example.com/mod/subpkg", version=None, artifact_dir="out/")`
- **THEN** the system loads a matching artifact that contains package `example.com/mod/subpkg`
- **AND THEN** the call returns a handle bound to package `example.com/mod/subpkg`

#### Scenario: Import chooses a specific version when provided
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="v1.2.3", artifact_dir="out/")`
- **THEN** the system MUST load version `v1.2.3` for that module/package (if present)

#### Scenario: Import omits version but follows already-loaded module version
- **WHEN** Python imports `example.com/mod` at version `v1.2.0`
- **AND WHEN** Python imports `example.com/mod/subpkg` with `version=None`
- **THEN** the second import resolves to version `v1.2.0` (the already-loaded module version)
- **AND THEN** the import does not fail with `AmbiguousArtifactError` even if multiple artifact versions exist on disk

#### Scenario: Import fails when version is omitted but ambiguous
- **WHEN** Python calls `usegolib.import_("example.com/mod", version=None, artifact_dir="out/")`
- **AND WHEN** `artifact_dir` contains more than one version for `example.com/mod` for the current OS/arch
- **AND WHEN** `example.com/mod` is not already loaded in the current Python process
- **THEN** the import MUST fail
- **AND THEN** the system SHALL raise `AmbiguousArtifactError`

### Requirement: Module Version Uniqueness Per Process
The system MUST NOT allow two different versions of the same Go module to be loaded within the same Python process.

#### Scenario: Version conflict is rejected
- **WHEN** Python imports `example.com/mod` at version `v1.2.0`
- **AND WHEN** Python imports `example.com/mod/subpkg` at version `v1.3.0`
- **THEN** the second import MUST fail
- **AND THEN** the system SHALL raise `VersionConflictError`

### Requirement: Build Mode And Caching
The system SHALL build the Go module into a shared library and cache build artifacts to avoid rebuilding when inputs are unchanged.

#### Scenario: First import builds and caches
- **WHEN** Python imports a module that is not yet built on disk for the resolved version
- **THEN** the system builds a shared library for that module and version
- **AND THEN** the build artifact is stored in a cache location

#### Scenario: Subsequent import reuses cached artifact
- **WHEN** Python imports a module that already has a cached shared library for the resolved version
- **THEN** the system loads the cached artifact without rebuilding

### Requirement: ABI Encoding
All cross-language calls between Python and Go MUST be encoded using MessagePack.

#### Scenario: Successful call returns a structured response
- **WHEN** Python calls an exported Go function through a module handle
- **THEN** the request MUST be encoded as MessagePack
- **AND THEN** the response MUST be MessagePack and indicate either a result or an error

### Requirement: Type Bridge Level 1 (V0)
For v0, the system SHALL support passing and returning Level 1 values across the Python/Go boundary: `nil`, `bool`, integers, floats, `string`, `bytes`, and slices of these.

#### Scenario: Passing bytes and receiving bytes
- **WHEN** Python passes a `bytes` value as an argument in a cross-language call
- **THEN** Go receives the argument as a byte sequence without loss
- **AND THEN** a byte sequence returned from Go is received by Python as `bytes`

#### Scenario: Passing a list of scalars
- **WHEN** Python passes a list containing only Level 1 scalar values
- **THEN** Go receives a slice containing the corresponding scalar values

### Requirement: Artifact Directory Layout (v0)
The builder SHALL write artifacts to disk using a stable layout so runtime lookup by module/package, version, and platform is deterministic.

#### Scenario: Builder output layout
- **WHEN** an artifact is built for module `example.com/mod` at version `vX.Y.Z` on OS `GOOS` and arch `GOARCH`
- **THEN** the builder writes `manifest.json` under `<out>/example.com/mod@vX.Y.Z/<GOOS>-<GOARCH>/manifest.json`
- **AND THEN** the shared library file path in the manifest is relative to that manifest directory

### Requirement: Module And Version Resolution (Build)
When building artifacts from a Go import path, the system SHALL resolve a concrete module version and record it in the artifact manifest.

#### Scenario: Version omitted defaults to @latest for remote modules
- **WHEN** `usegolib build` is invoked with a Go module import path and `version=None`
- **THEN** the system resolves the version query to `@latest`
- **AND THEN** the manifest `version` field contains the resolved concrete version

#### Scenario: Pinned version is used as-is for remote modules
- **WHEN** `usegolib build` is invoked with a Go module import path and `version="vX.Y.Z"`
- **THEN** the system builds using `vX.Y.Z`
- **AND THEN** the manifest `version` field MUST equal `vX.Y.Z`

#### Scenario: Local module directories use version "local"
- **WHEN** `usegolib build` is invoked with a local module directory
- **THEN** the manifest `version` field MUST be `"local"`

### Requirement: Import Builds Missing Artifacts (Dev Mode)
When `build_if_missing=True`, the system SHALL build a missing artifact into the artifact root and then load it.

When `build_if_missing=None` (auto), the system SHALL:
- build missing artifacts when `artifact_dir` is omitted (using the default artifact root)
- NOT build missing artifacts when `artifact_dir` is explicitly provided

#### Scenario: Import triggers build when artifact is missing
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=True)`
- **AND WHEN** no matching artifact exists under `artifact_dir` for the current OS/arch
- **THEN** the system builds the artifact into `artifact_dir`
- **AND THEN** the system loads the newly built artifact and returns a handle

#### Scenario: Import auto-builds when artifact_dir is omitted
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", build_if_missing=None)`
- **AND WHEN** no matching artifact exists under the default artifact root for the current OS/arch
- **THEN** the system builds the artifact into the default artifact root
- **AND THEN** the system loads the newly built artifact and returns a handle

#### Scenario: Import does not build by default when artifact_dir is provided
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=None)`
- **AND WHEN** no matching artifact exists under `artifact_dir` for the current OS/arch
- **THEN** the call fails with `ArtifactNotFoundError`

#### Scenario: Import does not rebuild when artifact exists
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=True)`
- **AND WHEN** a matching artifact already exists under `artifact_dir` for the current OS/arch
- **THEN** the system loads the existing artifact without rebuilding

### Requirement: Build Reuse And Locking
The builder SHALL reuse an existing artifact output when present (unless forced) and SHALL use file locking per artifact output directory to prevent concurrent writes.

#### Scenario: Build reuses existing artifact
- **WHEN** `usegolib build` is invoked for a module/version whose artifact already exists in `<out>`
- **THEN** the builder MUST return successfully without rebuilding

#### Scenario: Build uses a per-artifact lock
- **WHEN** two processes concurrently build the same module/version into the same `<out>`
- **THEN** only one process performs the build at a time
- **AND THEN** both processes complete without corrupting the output

### Requirement: Local Build Input Fingerprint
For local module directory builds, the system SHALL compute an input fingerprint and record it in the artifact manifest. Reuse MUST only occur when the fingerprint is unchanged.

#### Scenario: Local build writes fingerprint
- **WHEN** `usegolib build` is invoked with a local module directory
- **THEN** the system writes `input_fingerprint` into `manifest.json`

#### Scenario: Local source change triggers rebuild
- **WHEN** `usegolib build` is invoked with a local module directory and an artifact already exists
- **AND WHEN** the local module directory contents change
- **THEN** the builder MUST rebuild the artifact even if `manifest.json` already exists

### Requirement: Type Bridge Level 2 (V0.x)
The system SHALL support passing and returning Level 2 values across the Python/Go boundary: `map[string]T` where `T` is a Level 1 scalar or a slice of Level 1 scalars.

#### Scenario: Passing map[string]int64
- **WHEN** Python passes a dict of `str -> int` values
- **THEN** Go receives the argument as `map[string]int64` without loss

#### Scenario: Returning map[string][]byte
- **WHEN** a Go function returns `map[string][]byte`
- **THEN** Python receives it as a dict mapping `str -> bytes`

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

### Requirement: Export Scan Correctness (Build)
When building artifacts, the system SHALL discover exported top-level functions and their parameter/return types from Go source in a way that is robust to valid Go syntax and formatting (including grouped parameters).

#### Scenario: Grouped parameters are supported
- **WHEN** a Go package declares `func AddGrouped(a, b int64) int64`
- **THEN** the builder includes `AddGrouped` as a callable symbol

#### Scenario: Methods and generics are ignored
- **WHEN** a Go package declares an exported method `func (T) M(...) ...` or a generic function `func F[T any](...) ...`
- **THEN** the builder MUST NOT include those as callable symbols in v0

### Requirement: Type Bridge Level 3 Phase A (Record Structs) (V0.x)
The system SHALL support passing and returning named struct types as "record structs" across the Python/Go boundary, represented as maps from exported field keys to values.

For Level 3 Phase A, struct field values MUST be limited to supported Level 1, Level 2, and Level 3 Phase A types.

Record struct keys MUST follow the canonical key selection rules (tags) when tags are present.

#### Scenario: Passing a record struct value
- **WHEN** Python passes a dict for a Go parameter whose type is a named struct
- **THEN** Go receives the argument as the corresponding struct value
- **AND THEN** the struct's exported fields are populated from the dict keys

#### Scenario: Returning a record struct value
- **WHEN** a Go function returns a named struct value
- **THEN** Python receives it as a dict mapping canonical field keys to values

#### Scenario: Missing required fields are rejected
- **WHEN** a Go function parameter type is a named struct
- **AND WHEN** Python passes a dict missing a required exported field
- **THEN** the runtime MUST raise `UnsupportedTypeError` before invoking the shared library

#### Scenario: Nested record structs are supported
- **WHEN** Python passes a dict for a Go parameter whose type is a named struct
- **AND WHEN** that struct contains exported fields whose types are named structs
- **THEN** nested dict values are converted recursively to the nested struct values

#### Scenario: Containers of record structs are supported
- **WHEN** Python passes a list or dict of record structs for a Go parameter whose type is `[]Struct` or `map[string]Struct`
- **THEN** Go receives the argument as the corresponding slice/map of struct values

### Requirement: Schema Exchange (Import) (V0.x)
When importing an artifact, the system SHALL load a schema describing callable symbols and named struct types so the runtime can validate values before calling into the Go shared library.

#### Scenario: Manifest includes struct field schema
- **WHEN** an artifact is built for a module/package that defines named structs
- **THEN** the emitted `manifest.json` includes a schema describing exported struct fields and their types

#### Scenario: Runtime validates struct field types before call
- **WHEN** Python calls an exported function that accepts a record struct argument
- **AND WHEN** the provided dict contains a field value that does not match the schema type
- **THEN** the call fails with `UnsupportedTypeError` before invoking the shared library

### Requirement: Typed Struct Keys (Tags) (V0.x)
When using record structs, the system SHALL support mapping Python dict keys to Go struct fields using either the exported Go field name or supported tag keys.

Supported tags (in order of precedence for canonical keys) are:
1. `msgpack:"name,omitempty"`
2. `json:"name,omitempty"`

#### Scenario: Passing tag-keyed record structs
- **WHEN** a Go struct field has tag `json:"first_name"`
- **AND WHEN** Python passes a dict containing key `"first_name"`
- **THEN** Go receives the struct field populated as if the Python key were the exported field name

#### Scenario: Returning canonical keys
- **WHEN** a Go struct field has tag `msgpack:"age"`
- **AND WHEN** a Go function returns that struct value
- **THEN** Python receives the field under key `"age"` (canonical key), not the exported Go field name

### Requirement: Schema Validation For Results (V0.x)
When schema exchange is available in the artifact manifest, the runtime SHALL validate successful call results against the schema before returning them to user code.

#### Scenario: Runtime rejects schema-invalid results
- **WHEN** a successful call returns a value that does not conform to the schema result type
- **THEN** the runtime raises `UnsupportedTypeError` with a `schema:` prefixed message

### Requirement: Typed Adapter For time.Time (V0.x)
The system SHALL support `time.Time` values in supported signatures and typed structs by encoding/decoding them as RFC3339Nano strings across the ABI.

#### Scenario: Passing time.Time as a string
- **WHEN** a Go function parameter type is `time.Time`
- **AND WHEN** Python passes a string formatted as RFC3339Nano
- **THEN** Go receives the corresponding `time.Time` value

#### Scenario: Returning time.Time as a string
- **WHEN** a Go function returns a `time.Time`
- **THEN** Python receives it as an RFC3339Nano string

### Requirement: Typed Adapter For time.Duration (V0.x)
The system SHALL support `time.Duration` values in supported signatures and typed structs by encoding/decoding them as integers representing nanoseconds across the ABI.

#### Scenario: Passing time.Duration as an int
- **WHEN** a Go function parameter type is `time.Duration`
- **AND WHEN** Python passes an integer value (nanoseconds)
- **THEN** Go receives the corresponding `time.Duration` value

#### Scenario: Returning time.Duration as an int
- **WHEN** a Go function returns a `time.Duration`
- **THEN** Python receives it as an integer value (nanoseconds)

### Requirement: Typed Struct Tag Options (omitempty and ignore) (V0.x)
When exchanging typed struct values, the system SHALL respect common tag options:

- `omitempty`: fields tagged `omitempty` are not required to be present in Python dict inputs, and may be omitted from record-struct outputs when the field value is empty.
- ignore: fields tagged with `msgpack:"-"` (or, if no msgpack tag is present, `json:"-"`) MUST NOT be included in schema exchange and MUST NOT be present in record-struct outputs.

#### Scenario: omitempty fields are optional
- **WHEN** a Go struct field is tagged `json:"nick,omitempty"`
- **AND WHEN** Python passes a dict that omits `nick`
- **THEN** the runtime accepts the value (no missing-field error)

#### Scenario: omitempty fields may be omitted on output
- **WHEN** a Go struct field is tagged `json:"nick,omitempty"`
- **AND WHEN** the returned struct has an empty `nick` value
- **THEN** Python does not receive the `nick` key in the record-struct dict

#### Scenario: Ignored fields are excluded
- **WHEN** a Go struct field is tagged `json:"-"`
- **THEN** the builder does not include the field in the manifest schema
- **AND THEN** record-struct outputs do not include that field

### Requirement: Typed Struct Embedded Fields (V0.x)
The system SHALL include exported embedded (anonymous) struct fields in schema exchange so runtime validation can accept record structs containing embedded fields.

Note: embedded fields are represented as a nested record-struct field keyed by the embedded field name (type name) unless a canonical tag key overrides it.

#### Scenario: Embedded fields appear in schema and outputs
- **WHEN** a Go struct contains an exported embedded field whose type is a named struct
- **THEN** the manifest schema includes that embedded field
- **AND THEN** record-struct outputs include a nested dict under the embedded field key

### Requirement: Python Typed Struct Wrappers (V0.x)
When schema exchange is available in the artifact manifest, the runtime SHALL be able to generate Python dataclasses corresponding to named Go structs and provide a typed calling surface.

The typed calling surface SHALL:
- accept generated dataclass instances as inputs wherever a record struct value is expected
- decode successful record-struct results into generated dataclass instances when the schema indicates a struct result type

#### Scenario: Dataclass instances are accepted as inputs
- **WHEN** a Go function parameter type is a named struct
- **AND WHEN** Python passes an instance of the generated dataclass for that struct
- **THEN** the runtime encodes it as a record struct dict using canonical keys and calls into the shared library successfully

#### Scenario: Struct results decode to dataclasses
- **WHEN** a Go function returns a named struct value
- **AND WHEN** Python calls the function through the typed calling surface
- **THEN** Python receives an instance of the corresponding generated dataclass

### Requirement: Typed Adapter For uuid.UUID (V0.x)
The system SHALL support `github.com/google/uuid.UUID` values in supported signatures and typed structs by encoding/decoding them as strings across the ABI.

#### Scenario: Passing uuid.UUID as a string
- **WHEN** a Go function parameter type is `uuid.UUID`
- **AND WHEN** Python passes a UUID string
- **THEN** Go receives the corresponding `uuid.UUID` value

#### Scenario: Returning uuid.UUID as a string
- **WHEN** a Go function returns a `uuid.UUID`
- **THEN** Python receives it as a UUID string

### Requirement: Python Bindings Generator (V0.x)
When schema exchange is available in an artifact manifest, the system SHALL be able to generate a static Python module for a specified Go package containing dataclasses for named structs and a typed API wrapper for callable symbols.

#### Scenario: Generate bindings module
- **WHEN** the user runs `usegolib gen` with an artifact directory and package
- **THEN** the system writes a Python module containing struct dataclasses and typed API methods

#### Scenario: Generated API calls Go successfully
- **WHEN** the user imports the generated module and calls `load(...)` to obtain the API
- **AND WHEN** the user calls a generated method with supported values (including generated dataclasses)
- **THEN** the call succeeds and returns values matching the generated type annotations

### Requirement: Library SHA256 Verification (V0.x)
When loading an artifact, the runtime SHALL verify the shared library integrity by checking the library file SHA256 against `manifest.json`.

The manifest MUST include `library.sha256` as a 64-character lowercase hex digest.

#### Scenario: Correct SHA256 loads successfully
- **WHEN** the runtime loads an artifact whose library file SHA256 matches `library.sha256`
- **THEN** the runtime loads the shared library successfully

#### Scenario: Missing SHA256 is rejected
- **WHEN** the runtime loads an artifact whose manifest is missing `library.sha256`
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library

#### Scenario: Mismatched SHA256 is rejected
- **WHEN** the runtime loads an artifact whose library file SHA256 does not match `library.sha256`
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library

### Requirement: Manifest Version And Platform Validation (V0.x)
When loading an artifact, the runtime SHALL validate the artifact manifest fields are supported by this version of `usegolib` before attempting to load the shared library.

Supported values are:
- `manifest_version == 1`
- `abi_version == 0`

The runtime SHALL reject artifacts built for a different platform than the current host.

#### Scenario: Unsupported manifest version is rejected
- **WHEN** the runtime loads an artifact whose `manifest_version` is not supported
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library

#### Scenario: Unsupported ABI version is rejected
- **WHEN** the runtime loads an artifact whose `abi_version` is not supported
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library

#### Scenario: Wrong platform artifact is rejected
- **WHEN** the runtime loads an artifact whose `goos/goarch` do not match the current host
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library

### Requirement: Artifact Index Cache (V0.x)
To improve performance for large artifact roots, the runtime SHALL be allowed to create and use an index cache file under the artifact root for artifact discovery.

The index MUST NOT change the import resolution semantics: if a matching artifact exists under the artifact root, it MUST be found; if multiple versions exist and version is omitted, the import MUST remain ambiguous.

#### Scenario: Index is created on first import
- **WHEN** Python imports a module from an artifact root that does not yet contain an index
- **THEN** the runtime MAY create an index cache file under the artifact root
- **AND THEN** the import resolution behavior is unchanged

#### Scenario: Stale index entries are handled
- **WHEN** the artifact root contains an index that references missing manifest files
- **THEN** the runtime falls back to scanning and rebuilds the index
- **AND THEN** the import resolution behavior is unchanged

#### Scenario: Stale index does not hide ambiguity
- **WHEN** the artifact root contains an index that was created before a second version of an artifact was added
- **AND WHEN** Python imports with `version=None`
- **THEN** the import MUST still be ambiguous

### Requirement: Zig Download Verification (V0.x)
When bootstrapping Zig automatically, the builder SHALL verify the Zig download integrity and SHALL extract archives safely.

The builder MUST:
- fetch Zig download metadata only from `https://ziglang.org/...`
- download Zig archives only from `https://ziglang.org/...`
- verify the archive SHA256 using the digest provided by Zig's download metadata
- reject unsafe archive paths (absolute paths or path traversal) during extraction

#### Scenario: Mismatched Zig archive SHA256 is rejected
- **WHEN** the builder downloads a Zig archive whose SHA256 does not match the metadata digest
- **THEN** the builder SHALL raise `BuildError` and MUST NOT use the downloaded archive

#### Scenario: Unsafe archive paths are rejected
- **WHEN** a Zig archive contains an unsafe path (absolute or path traversal)
- **THEN** the builder SHALL raise `BuildError` and MUST NOT extract the unsafe entry

### Requirement: Go Object Handles And Exported Methods (V0.x)
The system SHALL support calling exported Go methods without serializing the receiver value on every call by using Go-side object handles.

The runtime SHALL expose a Python API to:
- create a Go-side object handle for a named struct type (`obj_new`)
- call exported methods on that handle (`obj_call`)
- free the handle (`obj_free`)

#### Scenario: Create object handle and call method
- **WHEN** Python creates a Go object handle for a named struct type
- **AND WHEN** Python calls an exported method on the object handle
- **THEN** the call succeeds and returns the method result

#### Scenario: Freeing an object handle makes it unusable
- **WHEN** Python frees a Go object handle
- **AND WHEN** Python calls a method on the freed handle
- **THEN** the call fails with an error

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

### Requirement: Missing Go Toolchain Hint (V0.x)
When the system needs to build artifacts using the Go toolchain and the `go` executable cannot be found, the system SHALL raise a `BuildError` with an actionable hint.

The hint SHOULD mention:
- installing Go and ensuring `go` is on `PATH`
- disabling auto-build via `build_if_missing=False` and using prebuilt artifacts/wheels

#### Scenario: Import auto-build fails because `go` is missing
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z")`
- **AND WHEN** the artifact is missing and auto-build is attempted
- **AND WHEN** `go` is not available on `PATH`
- **THEN** the call fails with `BuildError`
- **AND THEN** the error message includes a hint to install Go or disable auto-build

### Requirement: GoDoc To Python Docstrings (V0.x)
When building an artifact, the system SHALL extract Go doc comments for exported functions and methods and include them in the artifact schema.

When schema is present, the Python runtime SHALL attach docstrings to the dynamic callables it returns for exported functions and methods.

If GoDoc is missing for a callable, the runtime SHOULD still attach a signature-based docstring (so `help()` is informative).

Typed wrappers (`handle.typed()` and typed objects) SHALL preserve the docstrings of the underlying dynamic callables.

The bindgen generator SHOULD emit these docs as Python docstrings in generated modules.

#### Scenario: Runtime exposes GoDoc for a function
- **WHEN** an artifact manifest schema includes `doc` for a symbol
- **AND WHEN** the user imports the package and accesses the function
- **THEN** the returned callable has `__doc__` containing the Go doc comment

#### Scenario: Runtime provides signature docstring fallback
- **WHEN** an artifact manifest schema includes a symbol signature but has no `doc`
- **AND WHEN** the user accesses the callable
- **THEN** the returned callable has a non-empty `__doc__` containing a Go signature string

#### Scenario: Typed wrappers preserve docstrings
- **WHEN** a user accesses a callable via `handle.typed()`
- **THEN** the typed callable has the same `__doc__` content as the untyped callable

#### Scenario: Bindgen includes docstrings
- **WHEN** an artifact manifest schema includes `doc` for a symbol
- **AND WHEN** the user runs `usegolib bindgen`
- **THEN** the generated Python method includes a docstring derived from the Go doc comment

### Requirement: Opaque Pointer Results Use Object Handles (V0.x)
When a callable symbol or method returns `*T` and the struct type `T` has no exported fields in the manifest schema, the system SHALL represent that value as an object handle rather than a record-struct dict.

#### Scenario: Function returns *Opaque handle
- **WHEN** a Go function returns `*T`
- **AND WHEN** `T` has no exported fields
- **THEN** Python receives a `GoObject` that can be used to call exported methods on `T`

### Requirement: Error-Only Results Are Treated As Nil On Success
When a callable symbol or method returns only `error`, the system SHALL represent successful results as `nil` (Python `None`).

If the returned `error` is non-nil, the system SHALL report the failure via the ABI error envelope as `GoError`.

#### Scenario: Method returns only error and succeeds
- **WHEN** a Go method returns `error`
- **AND WHEN** the call succeeds (`error` is `nil`)
- **THEN** the Python result is `None`

#### Scenario: Method returns only error and fails
- **WHEN** a Go method returns `error`
- **AND WHEN** the call fails (`error` is non-nil)
- **THEN** the Python call raises `GoError`

### Requirement: Builder Retries Transient Go Network Failures
When building or rebuilding artifacts for remote modules, the builder SHALL retry transient Go module download failures and provide actionable remediation hints.

#### Scenario: Transient proxy failures are retried and may fall back to GOPROXY=direct
- **WHEN** a build executes Go commands that may download modules (for example `go mod download`, `go list`, or `go build`)
- **AND WHEN** the command fails due to a transient network/proxy error (for example `proxy.golang.org` timeouts)
- **THEN** the builder retries the command with a short backoff
- **AND THEN** if `GOPROXY` is not explicitly set, the builder MAY retry with `GOPROXY=direct`

#### Scenario: Failures include a hint for common network/proxy remediation
- **WHEN** a build fails due to a network/proxy error downloading Go modules
- **THEN** the builder raises `BuildError`
- **AND THEN** the error message includes a hint mentioning `GOPROXY=direct`


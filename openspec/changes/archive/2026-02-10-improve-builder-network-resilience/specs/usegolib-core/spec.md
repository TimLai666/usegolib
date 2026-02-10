## ADDED Requirements

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


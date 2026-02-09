"""Domain-specific errors for usegolib."""

from __future__ import annotations


class UseGoLibError(Exception):
    """Base error for usegolib."""


class ArtifactNotFoundError(UseGoLibError):
    """Raised when an expected artifact/manifest cannot be found."""


class VersionConflictError(UseGoLibError):
    """Raised when two versions of the same module would be loaded in one process."""


class AmbiguousArtifactError(UseGoLibError):
    """Raised when artifact resolution matches multiple candidates."""


class LoadError(UseGoLibError):
    """Raised when a shared library cannot be loaded."""


class BuildError(UseGoLibError):
    """Raised when building an artifact fails."""


class ABIEncodeError(UseGoLibError):
    """Raised when a request cannot be encoded to MessagePack."""


class ABIDecodeError(UseGoLibError):
    """Raised when a response cannot be decoded from MessagePack."""


class GoError(UseGoLibError):
    """Raised when Go returns an error payload."""


class GoPanicError(UseGoLibError):
    """Raised when Go panics and the bridge reports it."""


class UnsupportedTypeError(UseGoLibError):
    """Raised when an argument/result type is not supported by the type bridge."""


class UnsupportedSignatureError(UseGoLibError):
    """Raised when a Go symbol signature is not supported by the bridge."""

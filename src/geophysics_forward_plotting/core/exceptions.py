"""Framework-specific exceptions with actionable failure messages."""


class GeophysicsForwardPlottingError(Exception):
    """Base exception for the package."""


class ConfigurationError(GeophysicsForwardPlottingError):
    """Raised when a task or style configuration is invalid."""


class DataValidationError(GeophysicsForwardPlottingError):
    """Raised when input data cannot satisfy a plotting task."""


class SkillRegistrationError(GeophysicsForwardPlottingError):
    """Raised for duplicate or invalid skill registration."""


class SkillNotFoundError(GeophysicsForwardPlottingError):
    """Raised when no registered skill can handle a task."""


class BackendUnavailableError(GeophysicsForwardPlottingError):
    """Raised when an explicitly requested backend is unavailable."""


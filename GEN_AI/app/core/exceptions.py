"""Custom exception types used across the application."""


class ExternalServiceError(RuntimeError):
    """Raised when an upstream AI provider returns an unexpected error."""


class AI4BharatAPIError(ExternalServiceError):
    """Wraps errors from the AI4Bharat NLP pipeline."""


class RevidAPIError(ExternalServiceError):
    """Wraps errors from the Revid.ai video generation API (deprecated)."""


class FalAPIError(ExternalServiceError):
    """Wraps errors from the fal.ai video generation API."""


class PetsBackendError(ExternalServiceError):
    """Wraps errors from the pets-backend GraphQL API."""

class FeatureFlagClientError(Exception):
    """Base exception for all Feature Flag SDK errors."""
    pass

class FeatureFlagNotFoundError(FeatureFlagClientError):
    """Raised when a feature flag is not found on the server (HTTP 404)."""
    pass

class FeatureFlagServerError(FeatureFlagClientError):
    """Raised when server returns HTTP 5xx or connection fails."""
    pass

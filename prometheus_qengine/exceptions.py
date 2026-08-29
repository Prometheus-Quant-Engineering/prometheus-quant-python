class PrometheusError(Exception):
    """Base exception for Prometheus SDK."""
    pass

class AuthenticationError(PrometheusError):
    """Raised when the API Key is invalid or missing."""
    pass

class InsufficientCreditsError(PrometheusError):
    """Raised when the account lacks compute credits (HTTP 402)."""
    pass

class EngineComputationError(PrometheusError):
    """Raised when the C++ engine fails to compute the matrix."""
    pass
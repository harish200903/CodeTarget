class AIServiceError(Exception):
    """Base exception for all AI subsystem errors."""
    def __init__(self, message: str = "AI service error occurred"):
        self.message = message
        super().__init__(self.message)


class AIConfigurationError(AIServiceError):
    """Raised when AI is disabled or API key is unconfigured."""
    def __init__(self, message: str = "AI subsystem is disabled or missing configuration."):
        super().__init__(message)


class AIProviderUnavailable(AIServiceError):
    """Raised when AI provider (e.g., Gemini API) is unreachable or errors out."""
    def __init__(self, message: str = "AI service provider is temporarily unavailable."):
        super().__init__(message)


class AIProviderTimeout(AIServiceError):
    """Raised when request to AI provider times out."""
    def __init__(self, message: str = "AI provider request timed out."):
        super().__init__(message)


class AIRateLimitExceeded(AIServiceError):
    """Raised when user exceeds AI rate limit."""
    def __init__(self, message: str = "AI rate limit exceeded. Please wait before making more requests."):
        super().__init__(message)


class AIResponseValidationError(AIServiceError):
    """Raised when model response fails Pydantic schema validation."""
    def __init__(self, message: str = "AI response format validation failed."):
        super().__init__(message)

class AutoHealError(Exception):
    """Base exception for AutoHeal DevOps Agent."""
    pass

class AIClientError(AutoHealError):
    """Raised when the AI API fails (e.g., authentication, rate limits)."""
    pass

class PromptError(AutoHealError):
    """Raised when there is an issue with prompt generation or templates."""
    pass

class ParseError(AutoHealError):
    """Raised when the AI response cannot be parsed or validated."""
    pass

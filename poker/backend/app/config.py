"""
Poker App Configuration and Logging Setup
"""
import os
import logging
import sys
from typing import Optional

# =============================================================================
# Environment-based Configuration
# =============================================================================

class Config:
    """Application configuration loaded from environment variables"""
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Game settings
    STARTING_CHIPS: int = int(os.getenv("STARTING_CHIPS", "1000"))
    SMALL_BLIND: int = int(os.getenv("SMALL_BLIND", "10"))
    BIG_BLIND: int = int(os.getenv("BIG_BLIND", "20"))
    MIN_RAISE: int = int(os.getenv("MIN_RAISE", "20"))
    
    # AI settings
    AI_DECISION_DELAY: float = float(os.getenv("AI_DECISION_DELAY", "0.5"))
    AI_BLIND_DELAY: float = float(os.getenv("AI_BLIND_DELAY", "0.3"))
    AI_DIFFICULTY: str = os.getenv("AI_DIFFICULTY", "mixed")  # easy, medium, hard, expert, mixed
    
    # Game cleanup
    GAME_CLEANUP_MINUTES: int = int(os.getenv("GAME_CLEANUP_MINUTES", "60"))
    MAX_AI_TURNS: int = int(os.getenv("MAX_AI_TURNS", "50"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "structured")  # "structured" or "simple"
    
    # Error tracking (Sentry)
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "production")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    
    # Performance monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
    SLOW_REQUEST_THRESHOLD_MS: float = float(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "500"))


# =============================================================================
# Centralized Logging Setup
# =============================================================================

class StructuredLogFormatter(logging.Formatter):
    """Structured JSON-like logging formatter for production"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Base message with timestamp, level, and message
        log_parts = [
            f"timestamp={self.formatTime(record)}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f"message={record.getMessage()}",
        ]
        
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_parts.append(f"correlation_id={record.correlation_id}")
        
        # Add exception info if present
        if record.exc_info:
            log_parts.append("exception=true")
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage",
                "correlation_id"
            ):
                log_parts.append(f"{key}={value}")
        
        return " ".join(log_parts)


def setup_logging(
    level: Optional[str] = None,
    format_type: Optional[str] = None
) -> logging.Logger:
    """
    Setup centralized logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to Config.LOG_LEVEL
        format_type: "structured" for production, "simple" for development
    
    Returns:
        Root logger instance
    """
    log_level = (level or Config.LOG_LEVEL).upper()
    fmt_type = (format_type or Config.LOG_FORMAT).lower()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Remove existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Set formatter based on format type
    if fmt_type == "structured":
        formatter = StructuredLogFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create logger for poker app
    logger = logging.getLogger("poker")
    logger.debug(f"Logging initialized with level={log_level}, format={fmt_type}")
    
    return logger


# Global logger instance (initialized lazily)
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get the poker app logger (initializes if needed)"""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


# =============================================================================
# Correlation ID Context
# =============================================================================

import contextvars

correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


def set_correlation_id(cid: str) -> None:
    """Set correlation ID for current context"""
    correlation_id_var.set(cid)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear correlation ID from current context"""
    correlation_id_var.set(None)


# Export all public symbols
__all__ = [
    "Config",
    "setup_logging",
    "get_logger",
    "StructuredLogFormatter",
    "set_correlation_id",
    "get_correlation_id",
    "clear_correlation_id",
]
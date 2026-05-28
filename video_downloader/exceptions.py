"""
Custom exceptions for video-downloader-skill.
"""


class DownloadError(Exception):
    """Base class for download-related errors."""
    pass


class NetworkError(DownloadError):
    """Network connection error."""
    pass


class PlatformError(DownloadError):
    """Platform-specific error."""
    pass


class AuthenticationError(DownloadError):
    """Authentication error."""
    pass


class ValidationError(DownloadError):
    """Input validation error."""
    pass


class AntiBotDetectionError(PlatformError):
    """Anti-bot detection triggered."""
    pass


class VideoUnavailableError(PlatformError):
    """Video is unavailable or has been removed."""
    pass


class UnsupportedPlatformError(ValidationError):
    """Platform is not supported."""
    pass


class RetryableError(DownloadError):
    """Error that can be retried."""
    pass


class NonRetryableError(DownloadError):
    """Error that should not be retried."""
    pass


class TimeoutError(NetworkError, RetryableError):
    """Request timeout error."""
    pass


class RateLimitError(NetworkError, RetryableError):
    """Rate limit exceeded."""
    pass

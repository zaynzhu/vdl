"""
Anti-bot detection strategy and recovery mechanisms.
"""

import asyncio
import random
from typing import Optional, Callable, Any
from .logger import logger
from .exceptions import AntiBotDetectionError, RateLimitError


class AntiBotStrategy:
    """
    Manages anti-bot detection and recovery strategies.
    
    Features:
    - Detection of anti-bot triggers
    - Automatic retry with increasing delays
    - Request header rotation
    - Fingerprint updates
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 5.0,
        max_delay: float = 60.0
    ):
        """
        Initialize anti-bot strategy.
        
        Args:
            max_retries: Maximum number of retries after detection
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.detection_count = 0
        
        logger.info(
            f"AntiBotStrategy initialized (max_retries={max_retries}, "
            f"base_delay={base_delay}s)"
        )
    
    def is_anti_bot_response(self, status_code: int, response_text: str = "") -> bool:
        """
        Detect if response indicates anti-bot detection.
        
        Args:
            status_code: HTTP status code
            response_text: Response body text
            
        Returns:
            True if anti-bot detection is suspected
        """
        # Common anti-bot indicators
        anti_bot_indicators = [
            status_code == 403,  # Forbidden
            status_code == 429,  # Too Many Requests
            status_code == 503,  # Service Unavailable
            'captcha' in response_text.lower(),
            'verify' in response_text.lower(),
            'robot' in response_text.lower(),
            'blocked' in response_text.lower(),
        ]
        
        detected = any(anti_bot_indicators)
        
        if detected:
            self.detection_count += 1
            logger.warning(
                f"Anti-bot detection suspected (status={status_code}, "
                f"detection_count={self.detection_count})"
            )
        
        return detected
    
    def calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate delay before retry using exponential backoff with jitter.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * 2^attempt
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        # Add jitter (±20%)
        jitter = delay * 0.2 * (random.random() * 2 - 1)
        delay += jitter
        
        # Ensure positive delay
        delay = max(delay, 1.0)
        
        logger.debug(f"Calculated retry delay: {delay:.2f}s (attempt {attempt + 1})")
        return delay
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        on_detection: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with automatic retry on anti-bot detection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            on_detection: Optional callback when detection occurs
            **kwargs: Keyword arguments for func
            
        Returns:
            Function result
            
        Raises:
            AntiBotDetectionError: If all retries exhausted
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                
                # Reset detection count on success
                if self.detection_count > 0:
                    logger.info("Request successful, resetting detection count")
                    self.detection_count = 0
                
                return result
                
            except (AntiBotDetectionError, RateLimitError) as e:
                last_error = e
                
                if attempt < self.max_retries:
                    # Calculate delay
                    delay = self.calculate_retry_delay(attempt)
                    
                    logger.warning(
                        f"Anti-bot detection triggered (attempt {attempt + 1}/"
                        f"{self.max_retries + 1}). Retrying in {delay:.1f}s..."
                    )
                    
                    # Call detection callback if provided
                    if on_detection:
                        try:
                            await on_detection(attempt, delay)
                        except Exception as callback_error:
                            logger.error(f"Detection callback failed: {callback_error}")
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Anti-bot detection: all {self.max_retries + 1} attempts failed"
                    )
                    raise AntiBotDetectionError(
                        f"Failed after {self.max_retries + 1} attempts: {e}"
                    )
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise AntiBotDetectionError("Unknown error in retry logic")
    
    def get_adaptive_delay(self) -> float:
        """
        Get adaptive delay based on detection history.
        
        Returns:
            Delay in seconds
        """
        if self.detection_count == 0:
            # No detection, use minimal delay
            return random.uniform(0.5, 1.5)
        elif self.detection_count < 3:
            # Some detection, use moderate delay
            return random.uniform(2.0, 5.0)
        else:
            # Frequent detection, use longer delay
            return random.uniform(5.0, 10.0)
    
    def should_rotate_headers(self) -> bool:
        """
        Determine if headers should be rotated.
        
        Returns:
            True if headers should be rotated
        """
        # Rotate headers after multiple detections
        return self.detection_count >= 2
    
    def should_update_fingerprint(self) -> bool:
        """
        Determine if browser fingerprint should be updated.
        
        Returns:
            True if fingerprint should be updated
        """
        # Update fingerprint after significant detections
        return self.detection_count >= 3
    
    def reset(self):
        """Reset detection state."""
        logger.info("Resetting anti-bot strategy state")
        self.detection_count = 0
    
    def get_status(self) -> dict:
        """
        Get current strategy status.
        
        Returns:
            Status dictionary
        """
        return {
            'detection_count': self.detection_count,
            'max_retries': self.max_retries,
            'should_rotate_headers': self.should_rotate_headers(),
            'should_update_fingerprint': self.should_update_fingerprint(),
            'adaptive_delay': self.get_adaptive_delay(),
        }


class PlatformSpecificStrategy:
    """
    Platform-specific anti-bot strategies.
    """
    
    @staticmethod
    def get_strategy_for_platform(platform: str) -> dict:
        """
        Get recommended strategy parameters for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Strategy parameters
        """
        strategies = {
            'douyin': {
                'max_retries': 5,
                'base_delay': 10.0,
                'requires_browser': True,
                'requires_signature': True,
                'signature_type': 'x-bogus',
            },
            'tiktok': {
                'max_retries': 5,
                'base_delay': 10.0,
                'requires_browser': True,
                'requires_signature': True,
                'signature_type': 'a-bogus',
            },
            'bilibili': {
                'max_retries': 3,
                'base_delay': 5.0,
                'requires_browser': False,
                'requires_signature': False,
            },
        }
        
        return strategies.get(platform, {
            'max_retries': 3,
            'base_delay': 5.0,
            'requires_browser': False,
            'requires_signature': False,
        })
    
    @staticmethod
    def get_detection_indicators(platform: str) -> list:
        """
        Get platform-specific detection indicators.
        
        Args:
            platform: Platform name
            
        Returns:
            List of detection indicator strings
        """
        indicators = {
            'douyin': [
                '验证码',
                '滑块验证',
                'captcha',
                'verify',
            ],
            'tiktok': [
                'captcha',
                'verify',
                'challenge',
            ],
            'bilibili': [
                '风控校验',
                '请求过于频繁',
                'rate limit',
            ],
        }
        
        return indicators.get(platform, ['captcha', 'verify', 'blocked'])

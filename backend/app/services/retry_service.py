# backend/app/services/retry_service.py

from typing import Any, Callable, Dict, Type, Union, Optional
import logging
import time
from functools import wraps
from googleapiclient.errors import HttpError

logger = logging.getLogger("retry_service")

class RetryService:
    """Handles error handling and retry logic for Google API operations."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def with_retry(
        self, 
        retryable_exceptions: tuple = (Exception,),
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None
    ):
        """
        Decorator to add retry logic to functions.
        
        Args:
            retryable_exceptions: Tuple of exception types to retry on
            max_retries: Maximum number of retries (overrides instance default)
            base_delay: Base delay between retries (overrides instance default)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute_with_retry(
                    func, 
                    *args, 
                    retryable_exceptions=retryable_exceptions,
                    max_retries=max_retries,
                    base_delay=base_delay,
                    **kwargs
                )
            return wrapper
        return decorator
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        retryable_exceptions: tuple = (Exception,),
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            retryable_exceptions: Tuple of exception types to retry on
            max_retries: Maximum number of retries
            base_delay: Base delay between retries
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function execution
            
        Raises:
            The last exception encountered after all retries are exhausted
        """
        max_retries = max_retries or self.max_retries
        base_delay = base_delay or self.base_delay
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt == max_retries:
                    logger.error(f"Function {func.__name__} failed after {max_retries} retries")
                    break
                
                # Calculate delay with exponential backoff
                delay = base_delay * (2 ** attempt)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                time.sleep(delay)
        
        # Re-raise the last exception
        raise last_exception
    
    @staticmethod
    def is_retryable_http_error(error: HttpError) -> bool:
        """
        Determine if an HTTP error is retryable.
        
        Args:
            error: The HTTP error to check
            
        Returns:
            True if the error is retryable, False otherwise
        """
        # Retry on server errors (5xx) and rate limiting (429)
        retryable_codes = [429, 500, 502, 503, 504]
        return error.status_code in retryable_codes
    
    def with_google_api_retry(self, max_retries: Optional[int] = None):
        """
        Decorator specifically for Google API calls with appropriate retry logic.
        
        Args:
            max_retries: Maximum number of retries
        """
        def should_retry(exception):
            if isinstance(exception, HttpError):
                return self.is_retryable_http_error(exception)
            # Also retry on generic network/connection errors
            return isinstance(exception, (ConnectionError, TimeoutError))
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                retries = max_retries or self.max_retries
                
                for attempt in range(retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        
                        if not should_retry(e) or attempt == retries:
                            break
                        
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(
                            f"Google API call {func.__name__} failed (attempt {attempt + 1}): {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        time.sleep(delay)
                
                raise last_exception
            return wrapper
        return decorator
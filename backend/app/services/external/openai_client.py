"""
OpenAI API client with retry logic, error handling, and token management.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
import tiktoken
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from .interfaces import OpenAIClientInterface, HealthCheckResult, ServiceStatus

logger = logging.getLogger(__name__)


class OpenAIClient(OpenAIClientInterface):
    """
    Production-ready OpenAI API client with comprehensive error handling.
    
    Features:
    - Automatic retry with exponential backoff
    - Token counting and validation
    - Circuit breaker pattern for resilience
    - Health monitoring and API key validation
    - Comprehensive logging for debugging
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o",
        max_tokens: int = 100000,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            default_model: Default model to use
            max_tokens: Maximum tokens per request
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__(service_name="OpenAI", timeout=timeout)
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.default_model = default_model
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided - client will not function")
            self.client = None
            self.async_client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=timeout,
                max_retries=max_retries,
            )
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=timeout,
                max_retries=max_retries,
            )
        
        # Token encoders for different models
        self._encoders = {}
        
    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """Get token encoder for a model, with caching."""
        if model not in self._encoders:
            try:
                self._encoders[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to gpt-4 encoder for unknown models
                logger.warning(f"Unknown model {model}, using gpt-4 encoder")
                self._encoders[model] = tiktoken.encoding_for_model("gpt-4")
        return self._encoders[model]
    
    def count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        """
        Count tokens in text for the given model.
        
        Args:
            text: Text to count tokens for
            model: Model to use for token counting
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            encoder = self._get_encoder(model)
            return len(encoder.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Rough fallback estimation (4 chars per token average)
            return len(text) // 4
    
    def count_message_tokens(
        self, messages: List[Dict[str, str]], model: str = "gpt-4o"
    ) -> int:
        """
        Count tokens in a list of messages.
        
        Args:
            messages: Messages in OpenAI format
            model: Model to use for token counting
            
        Returns:
            Total token count including message overhead
        """
        if not messages:
            return 0
        
        try:
            encoder = self._get_encoder(model)
            
            # Calculate tokens for each message
            total_tokens = 0
            for message in messages:
                # Message overhead tokens (role, content structure)
                total_tokens += 4
                
                for key, value in message.items():
                    if isinstance(value, str):
                        total_tokens += len(encoder.encode(value))
                    if key == "name":
                        total_tokens -= 1  # Name field is special
            
            # Add conversation overhead
            total_tokens += 2
            
            return total_tokens
            
        except Exception as e:
            logger.error(f"Error counting message tokens: {e}")
            # Fallback estimation
            text = " ".join(msg.get("content", "") for msg in messages)
            return self.count_tokens(text, model)
    
    async def validate_api_key(self) -> bool:
        """
        Validate the OpenAI API key by making a minimal API call.
        
        Returns:
            True if API key is valid
        """
        if not self.async_client:
            return False
        
        try:
            # Make a minimal API call to validate the key
            await self.async_client.models.list()
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def health_check(self) -> HealthCheckResult:
        """
        Check the health of the OpenAI API.
        
        Returns:
            HealthCheckResult with service status
        """
        if not self.async_client:
            return HealthCheckResult(
                status=ServiceStatus.UNHEALTHY,
                error_message="No API key configured"
            )
        
        start_time = time.time()
        
        try:
            # Test with a minimal completion request
            response = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use cheaper model for health check
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=1,
                ),
                timeout=10.0
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            self.record_success()
            
            return HealthCheckResult(
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                metadata={
                    "model_used": "gpt-3.5-turbo",
                    "completion_id": response.id,
                }
            )
            
        except asyncio.TimeoutError:
            self.record_failure()
            return HealthCheckResult(
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=int((time.time() - start_time) * 1000),
                error_message="Request timeout"
            )
        except Exception as e:
            self.record_failure()
            return HealthCheckResult(
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=int((time.time() - start_time) * 1000),
                error_message=str(e)
            )
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a completion using OpenAI API with retry logic.
        
        Args:
            messages: List of messages in OpenAI format
            model: Model to use (defaults to instance default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters for the API
            
        Returns:
            Dict containing the API response and metadata
            
        Raises:
            Exception: If API call fails after retries
        """
        if not self.async_client:
            raise ValueError("OpenAI client not initialized - check API key")
        
        if self.is_circuit_breaker_open():
            raise Exception("OpenAI service circuit breaker is open")
        
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        
        # Validate token count
        input_tokens = self.count_message_tokens(messages, model)
        if input_tokens > self.max_tokens:
            raise ValueError(
                f"Input tokens ({input_tokens}) exceed limit ({self.max_tokens})"
            )
        
        logger.info(
            f"Generating completion with {model}, {input_tokens} input tokens, "
            f"max_tokens={max_tokens}, temperature={temperature}"
        )
        
        async def _make_request():
            start_time = time.time()
            
            try:
                response: ChatCompletion = await self.async_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
                response_time = time.time() - start_time
                
                # Extract completion details
                completion = response.choices[0].message.content
                usage = response.usage
                
                self.record_success()
                
                result = {
                    "completion": completion,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens if usage else input_tokens,
                        "completion_tokens": usage.completion_tokens if usage else 0,
                        "total_tokens": usage.total_tokens if usage else input_tokens,
                    },
                    "metadata": {
                        "response_time": response_time,
                        "completion_id": response.id,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                }
                
                logger.info(
                    f"Completion successful: {usage.total_tokens if usage else 'unknown'} "
                    f"total tokens, {response_time:.2f}s"
                )
                
                return result
                
            except Exception as e:
                self.record_failure()
                logger.error(f"OpenAI API error: {e}")
                raise
        
        # Use the retry mechanism from the base class
        return await self.with_retry(_make_request)
    
    async def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-ada-002",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text embedding using OpenAI API.
        
        Args:
            text: Text to embed
            model: Embedding model to use
            **kwargs: Additional parameters
            
        Returns:
            Dict containing embedding and metadata
        """
        if not self.async_client:
            raise ValueError("OpenAI client not initialized - check API key")
        
        if self.is_circuit_breaker_open():
            raise Exception("OpenAI service circuit breaker is open")
        
        async def _make_request():
            start_time = time.time()
            
            try:
                response = await self.async_client.embeddings.create(
                    model=model,
                    input=text,
                    **kwargs
                )
                
                response_time = time.time() - start_time
                
                self.record_success()
                
                return {
                    "embedding": response.data[0].embedding,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    "metadata": {
                        "response_time": response_time,
                        "dimensions": len(response.data[0].embedding),
                    }
                }
                
            except Exception as e:
                self.record_failure()
                logger.error(f"OpenAI embedding error: {e}")
                raise
        
        return await self.with_retry(_make_request)
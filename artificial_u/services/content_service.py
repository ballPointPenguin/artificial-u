import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional

import anthropic
import openai
from google.api_core import exceptions as google_exceptions
from ollama import ResponseError

from artificial_u.config import get_settings
from artificial_u.integrations import anthropic_client, gemini_client, ollama_client, openai_client
from artificial_u.utils.exceptions import ContentGenerationError

# TODO: Make these configurable
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 4096  # Increased from 1024 to allow for longer responses like topic lists


class ContentService:
    """
    Service for generating text content using various AI models/backends.
    Provides a model-agnostic interface.
    """

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        # Get settings instance
        settings = get_settings()
        self.default_backend = settings.content_backend
        self.default_model = settings.content_model
        self.content_logs_path = settings.CONTENT_LOGS_PATH

        # Configure retry settings from settings
        self.max_retries = settings.content_max_retries
        self.retry_delay = settings.content_retry_delay
        self.retry_exponential_base = settings.content_retry_exponential_base

        self.logger.info(
            f"ContentService initialized with default backend: {self.default_backend}, "
            f"default model: {self.default_model}"
        )

    def _determine_backend(self, model: str) -> str:
        """
        Determine the appropriate backend based on the model name.

        Args:
            model: The model name to analyze

        Returns:
            The determined backend name as a string

        Raises:
            ValueError: If the model is not suitable for text generation
        """
        if model.startswith("claude-"):
            return "anthropic"
        elif model.startswith("gpt-"):
            return "openai"
        elif model.startswith("gemini-"):
            return "gemini"
        elif model.startswith("imagen-"):
            self.logger.error(
                f"Model '{model}' is an image model, not suitable for text generation."
            )
            raise ValueError(f"Model '{model}' is for image generation.")
        else:
            return "ollama"  # Default assumption, adjust as needed

    def _categorize_error(self, error: Exception, backend: str) -> str:
        """
        Categorize an error to determine if it's retryable.

        Returns:
            str: 'transient', 'rate_limited', 'permanent', or 'configuration'
        """
        if backend == "anthropic":
            return self._categorize_anthropic_error(error)
        elif backend == "openai":
            return self._categorize_openai_error(error)
        elif backend == "gemini":
            return self._categorize_gemini_error(error)
        elif backend == "ollama":
            return self._categorize_ollama_error(error)

        # Default to transient for unknown errors (optimistic retrying)
        return "transient"

    def _categorize_anthropic_error(self, error: Exception) -> str:
        """Categorize Anthropic-specific errors."""
        if isinstance(error, anthropic.InternalServerError):
            # 529 errors are transient overloaded errors
            if hasattr(error, "response") and error.response and error.response.status_code == 529:
                return "transient"
            return "transient"
        elif isinstance(error, anthropic.RateLimitError):
            return "rate_limited"
        elif isinstance(error, anthropic.APITimeoutError):
            return "transient"
        elif isinstance(error, anthropic.APIConnectionError):
            return "transient"
        elif isinstance(error, anthropic.BadRequestError):
            return "permanent"
        elif isinstance(error, anthropic.AuthenticationError):
            return "configuration"
        elif isinstance(error, anthropic.PermissionDeniedError):
            return "configuration"

        # Check for 529 in error message as fallback
        error_str = str(error)
        if "529" in error_str and "overloaded" in error_str.lower():
            return "transient"

        return "transient"

    def _categorize_openai_error(self, error: Exception) -> str:
        """Categorize OpenAI-specific errors."""
        if isinstance(error, openai.APITimeoutError):
            return "transient"
        elif isinstance(error, openai.RateLimitError):
            return "rate_limited"
        elif isinstance(error, openai.APIConnectionError):
            return "transient"
        elif isinstance(error, openai.InternalServerError):
            return "transient"
        elif isinstance(error, openai.BadRequestError):
            return "permanent"
        elif isinstance(error, openai.AuthenticationError):
            return "configuration"
        elif isinstance(error, openai.PermissionDeniedError):
            return "configuration"

        return "transient"

    def _categorize_gemini_error(self, error: Exception) -> str:
        """Categorize Gemini-specific errors."""
        if isinstance(error, google_exceptions.ServiceUnavailable):
            return "transient"
        elif isinstance(error, google_exceptions.TooManyRequests):
            return "rate_limited"
        elif isinstance(error, google_exceptions.InternalServerError):
            return "transient"
        elif isinstance(error, google_exceptions.BadRequest):
            return "permanent"
        elif isinstance(error, google_exceptions.Unauthenticated):
            return "configuration"
        elif isinstance(error, google_exceptions.PermissionDenied):
            return "configuration"

        return "transient"

    def _categorize_ollama_error(self, error: Exception) -> str:
        """Categorize Ollama-specific errors."""
        if isinstance(error, ResponseError):
            error_str = str(error)
            if "timeout" in error_str.lower():
                return "transient"
            elif "rate limit" in error_str.lower():
                return "rate_limited"
            elif "connection" in error_str.lower():
                return "transient"

        return "transient"

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry a function with exponential backoff."""
        last_error = None
        backend = kwargs.get("backend", "unknown")

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_type = self._categorize_error(e, backend)

                # Don't retry for permanent or configuration errors
                if error_type in ["permanent", "configuration"]:
                    self.logger.info(
                        f"Non-retryable error detected ({error_type}), not retrying: {e}"
                    )
                    break

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.retry_exponential_base**attempt)
                    self.logger.info(
                        f"Attempt {attempt + 1} failed with {error_type} error: {e}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed. Last error: {e}")

        # If we get here, all attempts failed
        raise last_error

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        prefill: Optional[str] = None,
    ) -> str:
        """
        Generates text based on the provided prompt using the specified or default model.

        Args:
            prompt: The main text prompt for generation.
            model: The specific model name to use (e.g., 'claude-3-7-sonnet-latest',
            'gpt-4', 'gemini-1.5-pro'). If None, uses the default model from settings.
            system_prompt: An optional system prompt or instruction for the model.
            temperature: Optional temperature for sampling (model-dependent, default varies).
            max_tokens: Optional maximum number of tokens to generate
            (model-dependent, default varies).
            prefill: Optional assistant message prefill content (Anthropic only).
            Claude will continue from where this prefill text ends.

        Returns:
            The generated text content as a string.

        Raises:
            ValueError: If the specified or default model is not supported or configured.
            NotImplementedError: If the backend for the model is not implemented.
            ContentGenerationError: If the content generation fails.
        """
        target_model = model or self.default_model
        if not target_model:
            self.logger.error("No model specified and no default model configured.")
            raise ValueError("No model specified and no default model configured.")

        self.logger.info(
            f"Generating text for prompt: '{prompt[:500]}...' using model: {target_model}"
        )

        # Determine backend based on model name
        backend = self._determine_backend(target_model)

        # Map backends to their respective generation methods
        backend_methods = {
            "anthropic": self._generate_anthropic,
            "openai": self._generate_openai,
            "gemini": self._generate_gemini,
            "ollama": self._generate_ollama,
        }

        # Get the appropriate generation method
        if backend not in backend_methods:
            self.logger.error(f"Unsupported backend: {backend} for model {target_model}")
            raise NotImplementedError(f"Backend '{backend}' is not implemented.")

        try:
            generation_method = backend_methods[backend]
            return await self._retry_with_backoff(
                generation_method,
                prompt,
                target_model,
                system_prompt,
                temperature,
                max_tokens,
                prefill,
                backend=backend,
            )
        except Exception as e:
            self.logger.error(
                f"Error generating text with model {target_model} (backend {backend}): {e}",
                exc_info=True,
            )
            # Re-raise as a generic ContentGenerationError to be handled by the caller
            raise ContentGenerationError(
                f"Failed to generate content with model {target_model}."
            ) from e

    async def _log_content(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None,
        temperature: float | None,
        max_tokens: int | None,
        response: str,
        backend: str,
    ) -> None:
        """Log the content generation details to a file.

        Args:
            model: The model used for generation
            prompt: The input prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature setting
            max_tokens: Optional max tokens setting
            response: The generated response
            backend: The backend service used (anthropic, openai, etc.)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        # Structure the log data hierarchically
        log_data = {
            "metadata": {
                "timestamp": timestamp,
                "backend": backend,
                "model": model,
                "settings": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            },
            "content": {"system_prompt": system_prompt, "prompt": prompt, "response": response},
        }

        # Create a unique filename for this generation
        filename = f"{timestamp}_{backend}_{model.replace('/', '_')}.json"
        filepath = os.path.join(self.content_logs_path, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Content log saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save content log to {filepath}: {str(e)}")

    async def _generate_anthropic(
        self, prompt, model, system_prompt, temperature, max_tokens, prefill, **kwargs
    ):
        self.logger.info(f"Generating text with Anthropic model: {model}")
        try:
            messages = []
            if system_prompt:
                pass  # Anthropic uses 'system' parameter outside messages
            messages.append({"role": "user", "content": prompt})

            # Add prefill assistant message if provided
            if prefill:
                messages.append({"role": "assistant", "content": prefill})
            response = await anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS,
                messages=messages,
                system=system_prompt,
                temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
            )
            response_text = response.content[0].text
        except anthropic.APIError as e:
            # Let the retry logic handle this
            raise e

        self.logger.info(f"Received response from Anthropic: {response_text[:500]}")

        await self._log_content(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response=response_text,
            backend="anthropic",
        )

        return response_text

    async def _generate_openai(
        self, prompt, model, system_prompt, temperature, max_tokens, prefill, **kwargs
    ):
        self.logger.info(f"Generating text with OpenAI model: {model}")
        if prefill:
            self.logger.warning("Prefill parameter provided but not supported for OpenAI models")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Determine which parameters to use based on the model
            # Build base parameters
            completion_params = {
                "model": model,
                "messages": messages,
            }

            # Check if this is a newer model that requires special handling
            # Models that require max_completion_tokens: gpt-5-*, o1-*, o3-*
            # Note: gpt-5-nano also doesn't support custom temperature values
            newer_model_prefixes = ("gpt-5", "o1-", "o3-", "gpt-4o-2024-08-06")
            is_newer_model = any(model.startswith(prefix) for prefix in newer_model_prefixes)

            # Handle token limits
            if is_newer_model:
                completion_params["max_completion_tokens"] = (
                    max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS
                )
                self.logger.debug(f"Using max_completion_tokens parameter for model {model}")
            else:
                completion_params["max_tokens"] = (
                    max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS
                )
                self.logger.debug(f"Using max_tokens parameter for model {model}")

            # Handle temperature - gpt-5-nano and some other models don't support custom temperature
            # For now, we'll skip temperature for gpt-5-nano specifically
            if model == "gpt-5-nano":
                self.logger.debug(f"Skipping temperature parameter for {model} (not supported)")
            else:
                completion_params["temperature"] = (
                    temperature if temperature is not None else DEFAULT_TEMPERATURE
                )

            response = await openai_client.chat.completions.create(**completion_params)
            response_text = response.choices[0].message.content
        except openai.BadRequestError as e:
            # Log the specific error details for bad requests
            self.logger.error(f"OpenAI BadRequestError for model {model}: {str(e)}")
            self.logger.error(f"Request parameters used: {completion_params}")
            raise e
        except openai.APIError as e:
            # Let the retry logic handle this
            self.logger.error(f"OpenAI API error for model {model}: {str(e)}")
            raise e

        self.logger.info(f"Received response from OpenAI: {response_text[:500]}")

        await self._log_content(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response=response_text,
            backend="openai",
        )

        return response_text

    async def _generate_gemini(
        self, prompt, model, system_prompt, temperature, max_tokens, prefill, **kwargs
    ):
        self.logger.info(f"Generating text with Gemini model: {model}")
        if prefill:
            self.logger.warning("Prefill parameter provided but not supported for Gemini models")
        try:
            from google.genai import types

            # Build the content list with proper Part structure
            contents = [types.Part.from_text(text=prompt)]

            # Create generation config with all parameters including system_instruction
            config_params = {
                "temperature": temperature if temperature is not None else DEFAULT_TEMPERATURE,
                "max_output_tokens": max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS,
            }

            # Add system instruction to config if provided
            if system_prompt:
                config_params["system_instruction"] = system_prompt

            generation_config = types.GenerateContentConfig(**config_params)

            # Call the API with the config containing all parameters
            response = await gemini_client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=generation_config,
            )

            # Handle response parsing more robustly
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and candidate.content:
                    if hasattr(candidate.content, "parts") and candidate.content.parts:
                        # Extract text from the first part
                        first_part = candidate.content.parts[0]
                        if hasattr(first_part, "text") and first_part.text:
                            response_text = first_part.text
                        else:
                            self.logger.warning("No text found in response part")
                            response_text = ""
                    else:
                        self.logger.warning("No parts found in response content")
                        response_text = ""
                else:
                    self.logger.warning("No content found in response candidate")
                    response_text = ""
            else:
                self.logger.warning("No candidates found in Gemini response")
                response_text = ""
        except (google_exceptions.GoogleAPICallError, Exception) as e:
            # Let the retry logic handle this
            raise e

        self.logger.info(f"Received response from Gemini: {response_text[:500]}")

        await self._log_content(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response=response_text,
            backend="gemini",
        )

        return response_text

    async def _generate_ollama(
        self, prompt, model, system_prompt, temperature, max_tokens, prefill, **kwargs
    ):
        self.logger.info(f"Generating text with Ollama model: {model}")
        if prefill:
            self.logger.warning("Prefill parameter provided but not supported for Ollama models")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = await ollama_client.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": temperature if temperature is not None else DEFAULT_TEMPERATURE,
                    "num_predict": max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS,
                },
            )
            response_text = response.get("message", {}).get("content", "")
        except (ResponseError, Exception) as e:
            # Let the retry logic handle this
            raise e

        self.logger.info(f"Received response from Ollama: {response_text[:500]}")

        await self._log_content(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response=response_text,
            backend="ollama",
        )

        return response_text

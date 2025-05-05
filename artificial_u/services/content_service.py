import json
import logging
import os
from datetime import datetime
from typing import Optional

from google.genai import types

from artificial_u.config import get_settings
from artificial_u.integrations import anthropic_client, gemini_client, ollama_client, openai_client

# TODO: Make these configurable
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 1024


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

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generates text based on the provided prompt using the specified or default model.

        Args:
            prompt: The main text prompt for generation.
            model: The specific model name to use (e.g., 'claude-3-opus-20240229',
            'gpt-4', 'gemini-1.5-pro'). If None, uses the default model from settings.
            system_prompt: An optional system prompt or instruction for the model.
            temperature: Optional temperature for sampling (model-dependent, default varies).
            max_tokens: Optional maximum number of tokens to generate
            (model-dependent, default varies).

        Returns:
            The generated text content as a string.

        Raises:
            ValueError: If the specified or default model is not supported or configured.
            NotImplementedError: If the backend for the model is not implemented.
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
            return await generation_method(
                prompt, target_model, system_prompt, temperature, max_tokens
            )
        except Exception as e:
            self.logger.error(
                f"Error generating text with model {target_model} (backend {backend}): {e}",
                exc_info=True,
            )
            raise

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

    async def _generate_anthropic(self, prompt, model, system_prompt, temperature, max_tokens):
        self.logger.info(f"Generating text with Anthropic model: {model}")
        messages = []
        if system_prompt:
            pass  # Anthropic uses 'system' parameter outside messages
        messages.append({"role": "user", "content": prompt})
        response = await anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS,
            messages=messages,
            system=system_prompt,
            temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
        )
        response_text = response.content[0].text
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

    async def _generate_openai(self, prompt, model, system_prompt, temperature, max_tokens):
        self.logger.info(f"Generating text with OpenAI model: {model}")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS,
            temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
        )
        response_text = response.choices[0].message.content
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

    async def _generate_gemini(self, prompt, model, system_prompt, temperature, max_tokens):
        self.logger.info(f"Generating text with Gemini model: {model}")
        contents = [types.Content(parts=[types.Part.from_text(prompt)])]
        generation_config = types.GenerationConfig(
            temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
            max_output_tokens=max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS,
        )
        if system_prompt:
            generation_config.system_instruction = system_prompt
        response = await gemini_client.aio.models.generate_content(
            model=model,
            contents=contents,
            generation_config=generation_config,
        )

        if response.candidates and response.candidates[0].content:
            response_text = response.candidates[0].content.parts[0].text
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
        else:
            self.logger.warning("No content generated from Gemini model")
            return ""

    async def _generate_ollama(self, prompt, model, system_prompt, temperature, max_tokens):
        self.logger.info(f"Generating text with Ollama model: {model}")
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

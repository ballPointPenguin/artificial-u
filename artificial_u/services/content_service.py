import logging
from typing import Optional

from google.genai import types

from artificial_u.config import get_settings
from artificial_u.integrations import (
    anthropic_client,
    gemini_client,
    ollama_client,
    openai_client,
)


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
        self.logger.info(
            f"ContentService initialized with default backend: {self.default_backend}, "
            f"default model: {self.default_model}"
        )

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
            model: The specific model name to use (e.g., 'claude-3-opus-20240229', 'gpt-4', 'gemini-1.5-pro').
                   If None, uses the default model from settings.
            system_prompt: An optional system prompt or instruction for the model.
            temperature: Optional temperature for sampling (model-dependent, default varies).
            max_tokens: Optional maximum number of tokens to generate (model-dependent, default varies).

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
            f"Generating text for prompt (first 50 chars): '{prompt[:50]}...' using model: {target_model}"
        )

        # Determine backend based on model name (this might need refinement)
        if target_model.startswith("claude-"):
            backend = "anthropic"
        elif target_model.startswith("gpt-"):
            backend = "openai"
        elif target_model.startswith("gemini-"):
            backend = "gemini"
        elif target_model.startswith("imagen-"):
            self.logger.error(
                f"Model '{target_model}' is an image model, not suitable for text generation."
            )
            raise ValueError(f"Model '{target_model}' is for image generation.")
        else:
            backend = "ollama"  # Default assumption, adjust as needed

        try:
            if backend == "anthropic":
                return await self._generate_anthropic(
                    prompt, target_model, system_prompt, temperature, max_tokens
                )
            elif backend == "openai":
                return await self._generate_openai(
                    prompt, target_model, system_prompt, temperature, max_tokens
                )
            elif backend == "gemini":
                return await self._generate_gemini(
                    prompt, target_model, system_prompt, temperature, max_tokens
                )
            elif backend == "ollama":
                return await self._generate_ollama(
                    prompt, target_model, system_prompt, temperature, max_tokens
                )
            else:
                self.logger.error(
                    f"Unsupported backend: {backend} for model {target_model}"
                )
                raise NotImplementedError(f"Backend '{backend}' is not implemented.")
        except Exception as e:
            self.logger.error(
                f"Error generating text with model {target_model} (backend {backend}): {e}",
                exc_info=True,
            )
            raise

    async def _generate_anthropic(
        self, prompt, model, system_prompt, temperature, max_tokens
    ):
        messages = []
        if system_prompt:
            pass  # Anthropic uses 'system' parameter outside messages
        messages.append({"role": "user", "content": prompt})
        response = await anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens if max_tokens is not None else 1024,
            messages=messages,
            system=system_prompt,
            temperature=temperature if temperature is not None else 0.7,
        )
        return response.content[0].text

    async def _generate_openai(
        self, prompt, model, system_prompt, temperature, max_tokens
    ):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens if max_tokens is not None else 1024,
            temperature=temperature if temperature is not None else 0.7,
        )
        return response.choices[0].message.content

    async def _generate_gemini(
        self, prompt, model, system_prompt, temperature, max_tokens
    ):
        contents = [types.Content(parts=[types.Part.from_text(prompt)])]
        generation_config = types.GenerationConfig(
            temperature=temperature if temperature is not None else 0.7,
            max_output_tokens=max_tokens if max_tokens is not None else 1024,
        )
        if system_prompt:
            generation_config.system_instruction = system_prompt
        response = await gemini_client.aio.models.generate_content(
            model=model,
            contents=contents,
            generation_config=generation_config,
        )
        if response.candidates and response.candidates[0].content:
            return response.candidates[0].content.parts[0].text
        else:
            self.logger.warning("No content generated from Gemini model")
            return ""

    async def _generate_ollama(
        self, prompt, model, system_prompt, temperature, max_tokens
    ):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await ollama_client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": temperature if temperature is not None else 0.7,
                "num_predict": max_tokens if max_tokens is not None else 1024,
            },
        )
        return response.get("message", {}).get("content", "")

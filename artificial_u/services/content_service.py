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
    ) -> str:
        """
        Generates text based on the provided prompt using the specified or default model.

        Args:
            prompt: The main text prompt for generation.
            model: The specific model name to use (e.g., 'claude-3-opus-20240229', 'gpt-4', 'gemini-1.5-pro').
                   If None, uses the default model from settings.
            system_prompt: An optional system prompt or instruction for the model.

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
        # Example routing logic:
        if target_model.startswith("claude-"):
            backend = "anthropic"
        elif target_model.startswith("gpt-"):
            backend = "openai"
        elif target_model.startswith("gemini-"):
            backend = "gemini"
        elif target_model.startswith(
            "imagen-"
        ):  # Imagen is for images, handle explicitly or error
            self.logger.error(
                f"Model '{target_model}' is an image model, not suitable for text generation."
            )
            raise ValueError(f"Model '{target_model}' is for image generation.")
        else:
            # Assume Ollama or handle other custom/local models
            # This part might need more sophisticated logic based on your model naming conventions
            backend = "ollama"  # Default assumption, adjust as needed
            # Or maybe use self.default_backend if model doesn't indicate a specific provider?
            # backend = self.default_backend

        try:
            if backend == "anthropic":
                messages = []
                if system_prompt:
                    # Anthropic uses 'system' parameter outside messages
                    pass  # Handled in create call
                messages.append({"role": "user", "content": prompt})
                response = await anthropic_client.messages.create(
                    model=target_model,
                    max_tokens=1024,  # Consider making this configurable
                    messages=messages,
                    system=system_prompt,  # Pass system prompt here
                )
                return response.content[0].text

            elif backend == "openai":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                response = await openai_client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    max_tokens=1024,  # Consider making this configurable
                )
                return response.choices[0].message.content

            elif backend == "gemini":
                # Create content with the prompt
                contents = [types.Content(parts=[types.Part.from_text(prompt)])]

                # Configure generation parameters
                generation_config = types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                )

                # Add system prompt if provided
                if system_prompt:
                    generation_config.system_instruction = system_prompt

                # Generate content using the Gemini API
                response = await gemini_client.aio.models.generate_content(
                    model=target_model,
                    contents=contents,
                    generation_config=generation_config,
                )

                # Extract and return the generated text
                if response.candidates and response.candidates[0].content:
                    return response.candidates[0].content.parts[0].text
                else:
                    self.logger.warning("No content generated from Gemini model")
                    return ""

            elif backend == "ollama":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                response = await ollama_client.chat(
                    model=target_model,
                    messages=messages,
                )
                # Check response structure
                return response.get("message", {}).get("content", "")

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
            # Re-raise or return a specific error message
            raise

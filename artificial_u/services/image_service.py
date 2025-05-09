import logging
import uuid
from typing import List, Optional

import httpx  # Added httpx import
import openai  # Added openai import
from google.genai import types

from artificial_u.integrations import gemini_client, openai_client
from artificial_u.models.core import Professor
from artificial_u.prompts.image import format_professor_image_prompt
from artificial_u.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# Mapping for OpenAI DALL-E 3 sizes based on common aspect ratios
# Add more mappings if other models/ratios are supported
OPENAI_ASPECT_RATIO_TO_SIZE = {
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "9:16": "1024x1792",
}


class ImageService:
    """
    Service for generating images using various AI models and storing them.

    This service handles image generation through configured AI backends
    (e.g., Google Imagen, OpenAI DALL-E) and stores the resulting images in a
    configurable storage backend (MinIO/S3).
    """

    def __init__(self, storage_service: StorageService):
        """
        Initialize the image generation service.

        Args:
            storage_service: The storage service for persisting generated images
        """
        self.storage_service = storage_service

        # Get model name and determine backend from settings
        from artificial_u.config import get_settings

        self.settings = get_settings()
        self.model_name = self.settings.IMAGE_GENERATION_MODEL
        self.backend = self._determine_backend(self.model_name)

        logger.info(
            f"ImageService initialized with model: {self.model_name} (backend: {self.backend})"
        )

    def _determine_backend(self, model_name: str) -> str:
        """Determine the backend based on the model name."""
        if model_name.startswith("imagen-"):
            return "gemini"
        elif model_name.startswith("dall-e-") or model_name.startswith("gpt-"):
            return "openai"
        else:
            # Default or raise error if model is unknown/unsupported
            logger.error(
                f"Unknown or unsupported image model prefix for '{model_name}'. "
                "Cannot determine backend. Please check model name and update _determine_backend."
            )
            # Defaulting to Gemini might hide configuration issues, so let's raise an error.
            # Consider adding a default backend setting if preferred.
            raise ValueError(f"Unsupported image generation model: {model_name}")

    def _map_aspect_ratio_to_openai_size(self, aspect_ratio: str) -> str:
        """Maps a common aspect ratio string to OpenAI's required size string."""
        size = OPENAI_ASPECT_RATIO_TO_SIZE.get(aspect_ratio)
        if not size:
            logger.warning(
                f"Unsupported aspect ratio '{aspect_ratio}' for OpenAI. "
                f"Defaulting to 1:1 ('{OPENAI_ASPECT_RATIO_TO_SIZE['1:1']}'). "
                f"Supported ratios: {list(OPENAI_ASPECT_RATIO_TO_SIZE.keys())}"
            )
            return OPENAI_ASPECT_RATIO_TO_SIZE["1:1"]
        return size

    async def _generate_gemini_image(self, prompt: str, aspect_ratio: str) -> List[bytes]:
        """Generates image(s) using the Google Gemini (Imagen) backend."""
        # NOTE: This uses the synchronous SDK call as generate_images_async is not available.
        # Consider using asyncio.to_thread if this becomes a blocking bottleneck.
        try:
            # Changed from generate_images_async to generate_images
            response = gemini_client.models.generate_images(
                model=self.model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,  # Currently generating only 1 image
                    aspect_ratio=aspect_ratio,
                ),
            )
            if response.generated_images:
                return [img.image.image_bytes for img in response.generated_images]
            else:
                logger.warning("No images were generated by the Gemini API")
                return []
        except Exception as e:
            logger.error(f"Error calling Gemini image generation API: {e}", exc_info=True)
            return []  # Indicate failure

    async def _call_openai_api(
        self, prompt: str, aspect_ratio: str
    ) -> Optional[openai.types.images_response.ImagesResponse]:
        """Makes the API call to OpenAI's image generation service."""
        try:
            openai_size = self._map_aspect_ratio_to_openai_size(aspect_ratio)
            response = await openai_client.images.generate(
                model=self.model_name,
                prompt=prompt,
                n=1,  # Currently generating only 1 image
                size=openai_size,
                # quality="standard", # Optional: "hd" for higher quality/cost
                # style="vivid" # Optional: "natural"
            )
            return response
        except openai.BadRequestError as e:
            logger.error(f"OpenAI API Bad Request Error: {e}", exc_info=True)
            if e.response:
                logger.error(f"OpenAI Response Status: {e.response.status_code}")
                try:
                    logger.error(f"OpenAI Response Body: {e.response.json()}")
                except Exception:
                    logger.error(f"OpenAI Response Body: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling OpenAI image generation API: {e}", exc_info=True)
            return None

    def _extract_image_data(self, item) -> Optional[tuple]:
        """
        Extract image data from response item, supporting various formats.

        Returns:
            tuple: (method, data) where method is 'url' or 'base64' and data is the
                  corresponding URL or base64 string, or None if no data found
        """
        # Try different possible field names that OpenAI might use for URLs
        if hasattr(item, "url") and item.url:
            return ("url", item.url)
        elif hasattr(item, "image_url") and item.image_url:
            return ("url", item.image_url)
        elif hasattr(item, "b64_json") and item.b64_json:
            return ("base64", item.b64_json)

        # Try to extract URL from item attributes
        if hasattr(item, "__dict__"):
            item_dict = item.__dict__
            for key, value in item_dict.items():
                if "url" in key.lower() and isinstance(value, str) and value.startswith("http"):
                    return ("url", value)

        return None

    async def _fetch_image_from_url(self, url: str) -> Optional[bytes]:
        """Fetches image data from a URL."""
        try:
            logger.info(f"Fetching image from OpenAI URL: {url[:100]}...")
            async with httpx.AsyncClient() as client:
                image_response = await client.get(url, timeout=30.0)
                image_response.raise_for_status()

                image_bytes = image_response.content
                logger.info(f"Successfully fetched image data ({len(image_bytes)} bytes).")
                return image_bytes

        except httpx.RequestError as req_err:
            logger.error(f"Error fetching image from URL {url}: {req_err}")
        except httpx.HTTPStatusError as status_err:
            logger.error(
                f"HTTP error fetching image from URL {url}: "
                f"Status {status_err.response.status_code}, "
                f"Response: {status_err.response.text[:200]}"
            )
        except Exception as fetch_err:
            logger.error(f"Unexpected error fetching image from URL {url}: {fetch_err}")

        return None

    async def _generate_openai_image(self, prompt: str, aspect_ratio: str) -> List[bytes]:
        """Generates image(s) using the OpenAI (DALL-E) backend."""
        # Step 1: Call the OpenAI API
        response = await self._call_openai_api(prompt, aspect_ratio)
        if not response or not response.data:
            logger.warning("No image data returned by the OpenAI API.")
            return []

        # Step 2: Process the response data
        image_data_list = []
        for item in response.data:
            # Extract data using helper method
            result = self._extract_image_data(item)

            if not result:
                logger.warning("Could not extract image data from response item.")
                continue

            method, data = result

            if method == "url":
                # Fetch image from URL
                image_bytes = await self._fetch_image_from_url(data)
                if image_bytes:
                    image_data_list.append(image_bytes)
            elif method == "base64":
                # Decode base64 data
                try:
                    import base64

                    image_bytes = base64.b64decode(data)
                    image_data_list.append(image_bytes)
                except Exception as e:
                    logger.error(f"Failed to decode base64 image data: {e}")

        return image_data_list

    async def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> List[str]:
        """
        Generates an image based on the provided prompt using the configured AI model.

        Args:
            prompt: The text prompt to generate the image from
            aspect_ratio: The desired aspect ratio for the image (default: "1:1").
                          Supported values depend on the backend model.

        Returns:
            A list of storage keys (object names) for the generated images.
            Empty if generation failed.
        """
        logger.info(
            f"Generating image via {self.backend} backend (model: {self.model_name}) "
            f"with prompt: '{prompt[:1500]}...' (aspect ratio: {aspect_ratio})"
        )

        image_bytes_list: List[bytes] = []
        try:
            # --- Dispatch to backend ---
            if self.backend == "gemini":
                image_bytes_list = await self._generate_gemini_image(prompt, aspect_ratio)
            elif self.backend == "openai":
                image_bytes_list = await self._generate_openai_image(prompt, aspect_ratio)
            else:
                logger.error(f"Unsupported image generation backend: {self.backend}")
                return []  # No generation possible

            if not image_bytes_list:
                logger.warning(f"Backend '{self.backend}' returned no image data.")
                return []

            # --- Upload generated images to storage ---
            uploaded_keys = []
            bucket = self.storage_service.images_bucket

            for image_bytes in image_bytes_list:
                if not image_bytes:  # Skip if empty bytes received
                    continue

                # Generate a simple UUID filename
                file_name = f"{uuid.uuid4()}.png"

                # Upload to storage
                success, url = await self.storage_service.upload_file(
                    file_data=image_bytes,
                    bucket=bucket,
                    object_name=file_name,
                    content_type="image/png",  # Assuming PNG for both backends for now
                )

                if success:
                    uploaded_keys.append(file_name)
                    logger.info(f"Image uploaded to {bucket}/{file_name}, URL: {url}")
                else:
                    logger.error(f"Failed to upload image {file_name} to bucket {bucket}")

            if uploaded_keys:
                logger.info(
                    f"Successfully generated and uploaded {len(uploaded_keys)} "
                    f"image(s) via {self.backend}."
                )
            else:
                logger.warning(
                    f"Image generation via {self.backend} succeeded, but upload "
                    f"failed for all images."
                )

            return uploaded_keys

        except Exception as e:
            # Catch potential errors during dispatch or upload logic
            logger.error(f"Error during image generation/upload process: {str(e)}", exc_info=True)
            return []

    async def generate_professor_image(
        self, professor: Professor, aspect_ratio: str = "1:1"
    ) -> Optional[str]:
        """
        Generates a profile image for a given professor.

        Args:
            professor: The Professor object
            aspect_ratio: The desired aspect ratio for the image prompt

        Returns:
            The storage key of the generated image, or None if generation failed
        """
        # Generate a prompt specifically for this professor
        prompt = format_professor_image_prompt(professor, aspect_ratio=aspect_ratio)
        logger.info(f"Generating image for professor {professor.id} ({professor.name})")

        # Generate just one image for the professor's profile
        image_keys = await self.generate_image(prompt=prompt, aspect_ratio=aspect_ratio)

        if image_keys:
            logger.info(
                f"Successfully generated image for professor {professor.id}: {image_keys[0]}"
            )
            return image_keys[0]  # Return the first (and only) key
        else:
            logger.error(f"Failed to generate image for professor {professor.id}")
            return None

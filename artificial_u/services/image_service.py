import logging
import uuid
from enum import Enum
from typing import List, Optional

import httpx  # Added httpx import
import openai  # Added openai import
from google.genai import types
from google.genai.errors import ClientError, ServerError
from google.genai.types import Modality

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


class ImageGenerationErrorType(Enum):
    """Types of image generation errors for categorization."""

    TRANSIENT = "transient"  # Temporary errors that may succeed on retry
    PERMANENT = "permanent"  # Permanent errors that won't succeed on retry
    RATE_LIMITED = "rate_limited"  # Rate limiting errors
    CONFIGURATION = "configuration"  # Configuration or setup errors
    BACKEND_UNAVAILABLE = "backend_unavailable"  # Backend service unavailable


class ImageGenerationError(Exception):
    """Base exception for image generation errors."""

    def __init__(
        self,
        message: str,
        error_type: ImageGenerationErrorType,
        backend: str = None,
        original_error: Exception = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.backend = backend
        self.original_error = original_error


class ImageGenerationResult:
    """Result container for image generation attempts."""

    def __init__(
        self, success: bool, image_keys: List[str] = None, error: ImageGenerationError = None
    ):
        self.success = success
        self.image_keys = image_keys or []
        self.error = error


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
        if model_name.startswith("imagen-") or model_name.startswith("gemini-"):
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

    def _categorize_error(self, error: Exception, backend: str) -> ImageGenerationErrorType:
        """Categorize an error to determine if it's retryable."""
        if backend == "gemini":
            return self._categorize_gemini_error(error)
        elif backend == "openai":
            return self._categorize_openai_error(error)

        # Default to transient for unknown errors (optimistic retrying)
        return ImageGenerationErrorType.TRANSIENT

    def _extract_status_code(self, error: ServerError) -> Optional[int]:
        """Extract status code from ServerError."""
        status_code = getattr(error, "status_code", None)
        if status_code is None:
            # Try extracting from error message
            error_str = str(error)
            for code in [503, 429, 500, 502, 504, 400]:
                if str(code) in error_str:
                    return code
        return status_code

    def _categorize_gemini_error(self, error: Exception) -> ImageGenerationErrorType:
        """Categorize Gemini-specific errors."""
        if isinstance(error, ServerError):
            status_code = self._extract_status_code(error)

            if status_code == 503:
                return ImageGenerationErrorType.TRANSIENT
            elif status_code == 429:
                return ImageGenerationErrorType.RATE_LIMITED
            elif status_code in [500, 502, 504]:
                return ImageGenerationErrorType.TRANSIENT
            else:
                return ImageGenerationErrorType.PERMANENT
        elif isinstance(error, ClientError):
            return ImageGenerationErrorType.CONFIGURATION
        return ImageGenerationErrorType.TRANSIENT

    def _categorize_openai_error(self, error: Exception) -> ImageGenerationErrorType:
        """Categorize OpenAI-specific errors."""
        if isinstance(error, openai.APITimeoutError):
            return ImageGenerationErrorType.TRANSIENT
        elif isinstance(error, openai.RateLimitError):
            return ImageGenerationErrorType.RATE_LIMITED
        elif isinstance(error, openai.APIConnectionError):
            return ImageGenerationErrorType.BACKEND_UNAVAILABLE
        elif isinstance(error, openai.InternalServerError):
            return ImageGenerationErrorType.TRANSIENT
        elif isinstance(error, openai.BadRequestError):
            return ImageGenerationErrorType.PERMANENT
        return ImageGenerationErrorType.TRANSIENT

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

    def _use_generate_content_api(self, model_name: str) -> bool:
        """
        Determine if model uses the generate_content API (Gemini 3 Pro Image)
        or the generate_images API (Imagen 4.x).
        """
        # Gemini 3 Pro Image uses generate_content with multimodal response
        return model_name.startswith("gemini-3-") or model_name.startswith("gemini-2.5-flash-image")

    async def _generate_gemini_image_via_content(
        self, prompt: str, aspect_ratio: str
    ) -> List[bytes]:
        """
        Generates image(s) using the Gemini generate_content API.
        Used for gemini-3-pro-image-preview (Nano Banana Pro) and similar models.
        """
        try:
            # Use generate_content API with image modality
            response = await gemini_client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=[Modality.IMAGE],
                    # Note: aspect_ratio handling may differ - check API docs
                ),
            )

            # Extract image bytes from response parts
            image_bytes_list = []
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        if hasattr(candidate.content, "parts") and candidate.content.parts:
                            for part in candidate.content.parts:
                                # Check for inline_data (new API format)
                                if hasattr(part, "inline_data") and part.inline_data:
                                    if hasattr(part.inline_data, "data"):
                                        image_bytes_list.append(part.inline_data.data)
                                # Also check for legacy format if present
                                elif hasattr(part, "image_bytes") and part.image_bytes:
                                    image_bytes_list.append(part.image_bytes)

            if not image_bytes_list:
                logger.warning("No images were generated by the Gemini generate_content API")
            return image_bytes_list

        except Exception as e:
            logger.error(
                f"Error calling Gemini generate_content image API: {e}", exc_info=True
            )
            raise  # Re-raise to allow retry logic to handle it

    async def _generate_gemini_image_via_images(
        self, prompt: str, aspect_ratio: str
    ) -> List[bytes]:
        """
        Generates image(s) using the Gemini generate_images API.
        Used for imagen-4.x models.
        """
        try:
            # Use the async client for proper async operation
            response = await gemini_client.aio.models.generate_images(
                model=self.model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,  # Currently generating only 1 image
                    aspect_ratio=aspect_ratio,
                ),
            )
            if hasattr(response, "generated_images") and response.generated_images:
                # Extract image bytes more safely
                image_bytes_list = []
                for img in response.generated_images:
                    if hasattr(img, "image") and hasattr(img.image, "image_bytes"):
                        image_bytes_list.append(img.image.image_bytes)
                return image_bytes_list
            else:
                logger.warning("No images were generated by the Gemini generate_images API")
                return []
        except Exception as e:
            logger.error(f"Error calling Gemini generate_images API: {e}", exc_info=True)
            raise  # Re-raise to allow retry logic to handle it

    async def _generate_gemini_image(self, prompt: str, aspect_ratio: str) -> List[bytes]:
        """
        Generates image(s) using the Google Gemini backend.
        Automatically selects the appropriate API based on the model name.
        """
        if self._use_generate_content_api(self.model_name):
            logger.info(
                f"Using generate_content API for {self.model_name} "
                "(Gemini 3 Pro Image / multimodal)"
            )
            return await self._generate_gemini_image_via_content(prompt, aspect_ratio)
        else:
            logger.info(f"Using generate_images API for {self.model_name} (Imagen 4.x)")
            return await self._generate_gemini_image_via_images(prompt, aspect_ratio)

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
            raise  # Re-raise to allow retry logic to handle it
        except Exception as e:
            logger.error(f"Error calling OpenAI image generation API: {e}", exc_info=True)
            raise  # Re-raise to allow retry logic to handle it

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
            raise
        except httpx.HTTPStatusError as status_err:
            logger.error(
                f"HTTP error fetching image from URL {url}: "
                f"Status {status_err.response.status_code}, "
                f"Response: {status_err.response.text[:200]}"
            )
            raise
        except Exception as fetch_err:
            logger.error(f"Unexpected error fetching image from URL {url}: {fetch_err}")
            raise

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
                    raise

        return image_data_list

    async def _generate_with_backend(
        self, prompt: str, aspect_ratio: str, backend: str
    ) -> List[bytes]:
        """Generate image with a specific backend."""
        if backend == "gemini":
            return await self._generate_gemini_image(prompt, aspect_ratio)
        elif backend == "openai":
            return await self._generate_openai_image(prompt, aspect_ratio)
        else:
            raise ImageGenerationError(
                f"Unsupported backend: {backend}",
                ImageGenerationErrorType.CONFIGURATION,
                backend=backend,
            )

    async def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> ImageGenerationResult:
        """
        Generates an image based on the provided prompt using the configured AI model.

        Args:
            prompt: The text prompt to generate the image from
            aspect_ratio: The desired aspect ratio for the image (default: "1:1").
                          Supported values depend on the backend model.

        Returns:
            An ImageGenerationResult object containing either success with image keys
            or failure with error information.
        """
        logger.info(
            f"Generating image via {self.backend} backend (model: {self.model_name}) "
            f"with prompt: '{prompt[:100]}...' (aspect ratio: {aspect_ratio})"
        )

        # Try backend with retry logic
        try:
            image_bytes_list = await self._generate_with_backend(prompt, aspect_ratio, self.backend)

            if image_bytes_list:
                # Upload images to storage
                uploaded_keys = await self._upload_images(image_bytes_list)
                if uploaded_keys:
                    logger.info(f"Successfully generated {len(uploaded_keys)} image(s)")
                    return ImageGenerationResult(success=True, image_keys=uploaded_keys)
                else:
                    error = ImageGenerationError(
                        "Image generation succeeded but upload failed",
                        ImageGenerationErrorType.TRANSIENT,
                        backend=self.backend,
                    )
                    return ImageGenerationResult(success=False, error=error)
            else:
                error = ImageGenerationError(
                    f"Backend {self.backend} returned no image data",
                    ImageGenerationErrorType.BACKEND_UNAVAILABLE,
                    backend=self.backend,
                )
                return ImageGenerationResult(success=False, error=error)

        except Exception as e:
            error = ImageGenerationError(
                f"Image generation failed: {str(e)}",
                self._categorize_error(e, self.backend),
                backend=self.backend,
                original_error=e,
            )

            logger.error(f"Image generation failed completely: {error}")
            return ImageGenerationResult(success=False, error=error)

    async def _upload_images(self, image_bytes_list: List[bytes]) -> List[str]:
        """Upload image bytes to storage and return the keys."""
        uploaded_keys = []
        bucket = self.storage_service.images_bucket

        for image_bytes in image_bytes_list:
            if not image_bytes:  # Skip if empty bytes received
                continue

            # Generate a simple UUID filename
            file_name = f"{uuid.uuid4()}.png"

            try:
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
            except Exception as e:
                logger.error(f"Error uploading image {file_name}: {e}")

        return uploaded_keys

    async def generate_professor_image(
        self, professor: Professor, aspect_ratio: str = "1:1"
    ) -> ImageGenerationResult:
        """
        Generates a profile image for a given professor.

        Args:
            professor: The Professor object
            aspect_ratio: The desired aspect ratio for the image prompt

        Returns:
            An ImageGenerationResult object with success/failure information.
        """
        # Generate a prompt specifically for this professor
        prompt = format_professor_image_prompt(professor, aspect_ratio=aspect_ratio)
        logger.info(f"Generating image for professor {professor.id} ({professor.name})")

        # Generate image using the main generation method
        result = await self.generate_image(prompt=prompt, aspect_ratio=aspect_ratio)

        if result.success and result.image_keys:
            logger.info(
                f"Successfully generated image for professor {professor.id}: {result.image_keys[0]}"
            )
        else:
            logger.error(f"Failed to generate image for professor {professor.id}: {result.error}")

        return result

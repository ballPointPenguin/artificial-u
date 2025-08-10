"""
Tests for ContentService retry logic.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import openai
import pytest

from artificial_u.services.content_service import ContentService
from artificial_u.utils.exceptions import ContentGenerationError


class TestContentServiceRetry:
    """Test retry logic in ContentService."""

    @pytest.fixture
    def content_service(self):
        """Create a ContentService instance for testing."""
        with patch("artificial_u.config.get_settings") as mock_settings:
            mock_settings.return_value.content_max_retries = 3
            mock_settings.return_value.content_retry_delay = 0.1  # Fast for testing
            mock_settings.return_value.content_retry_exponential_base = 2.0
            mock_settings.return_value.content_backend = "anthropic"
            mock_settings.return_value.content_model = "claude-3-sonnet-20240229"
            mock_settings.return_value.CONTENT_LOGS_PATH = "/tmp"

            return ContentService()

    @pytest.mark.asyncio
    async def test_retry_on_anthropic_529_error(self, content_service):
        """Test that 529 overloaded errors are retried."""
        # Mock the anthropic client to fail twice with 529, then succeed
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Success response")]

        with patch(
            "artificial_u.integrations.anthropic_client.messages.create", new_callable=AsyncMock
        ) as mock_create:
            # First two calls fail with 529 error
            mock_response_529 = MagicMock()
            mock_response_529.status_code = 529
            error_529 = anthropic.InternalServerError(
                "Error code: 529 - {'type': 'error', 'error': {'type': 'overloaded_error', "
                "'message': 'Overloaded'}}",
                response=mock_response_529,
                body={
                    "type": "error",
                    "error": {"type": "overloaded_error", "message": "Overloaded"},
                },
            )

            # Set up side effect to fail twice, then succeed
            mock_create.side_effect = [error_529, error_529, mock_response]

            # This should succeed on the third attempt
            result = await content_service.generate_text(
                prompt="Test prompt", model="claude-3-sonnet-20240229"
            )

            assert result == "Success response"
            assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, content_service):
        """Test that permanent errors are not retried."""
        with patch(
            "artificial_u.integrations.anthropic_client.messages.create", new_callable=AsyncMock
        ) as mock_create:
            # Bad request error should not be retried
            mock_response = MagicMock()
            mock_response.status_code = 400
            error_400 = anthropic.BadRequestError(
                "Bad request", response=mock_response, body={"error": "Bad request"}
            )
            mock_create.side_effect = error_400

            with pytest.raises(ContentGenerationError):
                await content_service.generate_text(
                    prompt="Test prompt", model="claude-3-sonnet-20240229"
                )

            # Should only be called once
            assert mock_create.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_openai_timeout(self, content_service):
        """Test that OpenAI timeout errors are retried."""
        with patch(
            "artificial_u.integrations.openai_client.chat.completions.create",
            new_callable=AsyncMock,
        ) as mock_create:
            # First call fails with timeout, second succeeds
            error_timeout = openai.APITimeoutError("Request timed out")
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Success"))]

            # Set up side effect to fail once, then succeed
            mock_create.side_effect = [error_timeout, mock_response]

            result = await content_service.generate_text(prompt="Test prompt", model="gpt-4")

            assert result == "Success"
            assert mock_create.call_count == 2

    def test_error_categorization_anthropic(self, content_service):
        """Test error categorization for Anthropic errors."""
        # Test 529 error
        mock_response_529 = MagicMock()
        mock_response_529.status_code = 529
        error_529 = anthropic.InternalServerError(
            "Error code: 529 - overloaded", response=mock_response_529, body={"error": "overloaded"}
        )
        assert content_service._categorize_anthropic_error(error_529) == "transient"

        # Test rate limit error
        mock_response_rate = MagicMock()
        mock_response_rate.status_code = 429
        error_rate_limit = anthropic.RateLimitError(
            "Rate limited", response=mock_response_rate, body={"error": "rate_limited"}
        )
        assert content_service._categorize_anthropic_error(error_rate_limit) == "rate_limited"

        # Test bad request error
        mock_response_bad = MagicMock()
        mock_response_bad.status_code = 400
        error_bad_request = anthropic.BadRequestError(
            "Bad request", response=mock_response_bad, body={"error": "bad_request"}
        )
        assert content_service._categorize_anthropic_error(error_bad_request) == "permanent"

        # Test authentication error
        mock_response_auth = MagicMock()
        mock_response_auth.status_code = 401
        error_auth = anthropic.AuthenticationError(
            "Invalid API key", response=mock_response_auth, body={"error": "authentication_failed"}
        )
        assert content_service._categorize_anthropic_error(error_auth) == "configuration"

    def test_error_categorization_openai(self, content_service):
        """Test error categorization for OpenAI errors."""
        # Test timeout error
        error_timeout = openai.APITimeoutError("Request timed out")
        assert content_service._categorize_openai_error(error_timeout) == "transient"

        # Test rate limit error
        mock_response_rate = MagicMock()
        mock_response_rate.status_code = 429
        error_rate_limit = openai.RateLimitError(
            "Rate limited", response=mock_response_rate, body={"error": "rate_limited"}
        )
        assert content_service._categorize_openai_error(error_rate_limit) == "rate_limited"

        # Test bad request error
        mock_response_bad = MagicMock()
        mock_response_bad.status_code = 400
        error_bad_request = openai.BadRequestError(
            "Bad request", response=mock_response_bad, body={"error": "bad_request"}
        )
        assert content_service._categorize_openai_error(error_bad_request) == "permanent"

        # Test authentication error
        mock_response_auth = MagicMock()
        mock_response_auth.status_code = 401
        error_auth = openai.AuthenticationError(
            "Invalid API key", response=mock_response_auth, body={"error": "authentication_failed"}
        )
        assert content_service._categorize_openai_error(error_auth) == "configuration"

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, content_service):
        """Test that max retries are respected."""
        with patch(
            "artificial_u.integrations.anthropic_client.messages.create", new_callable=AsyncMock
        ) as mock_create:
            # Always fail with 529 error
            mock_response = MagicMock()
            mock_response.status_code = 529
            error_529 = anthropic.InternalServerError(
                "Error code: 529 - overloaded", response=mock_response, body={"error": "overloaded"}
            )
            mock_create.side_effect = error_529

            with pytest.raises(ContentGenerationError):
                await content_service.generate_text(
                    prompt="Test prompt", model="claude-3-sonnet-20240229"
                )

            # Should be called exactly max_retries times
            assert mock_create.call_count == content_service.max_retries

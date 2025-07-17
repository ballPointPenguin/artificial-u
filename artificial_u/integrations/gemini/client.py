from google import genai

from artificial_u.config import get_settings

settings = get_settings()
# Initialize the Gemini client with API key
# The async client is accessed via client.aio for async operations
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

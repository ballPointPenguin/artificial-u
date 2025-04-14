from google import genai

from artificial_u.config import get_settings

settings = get_settings()
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

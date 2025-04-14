import openai

from artificial_u.config import get_settings

settings = get_settings()
client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
# Use AsyncOpenAI for compatibility with async services

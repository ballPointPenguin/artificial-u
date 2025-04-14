import anthropic

from artificial_u.config.settings import get_settings

settings = get_settings()
client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
# Use AsyncAnthropic for compatibility with async services

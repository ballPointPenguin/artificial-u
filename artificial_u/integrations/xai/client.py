import openai

from artificial_u.config import get_settings

settings = get_settings()
# xAI's chat API is OpenAI-compatible, so reuse the OpenAI SDK pointed at the xAI base URL.
# A placeholder key keeps import working without XAI_API_KEY; the content service checks
# for the real key before generating.
client = openai.AsyncOpenAI(api_key=settings.XAI_API_KEY or "unset", base_url=settings.XAI_BASE_URL)

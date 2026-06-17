from langchain_openai import ChatOpenAI
from app.config import Settings


def get_llm_client(settings: Settings) -> ChatOpenAI:
    """
    Initializes and returns a LangChain ChatOpenAI (or OpenAI-compatible) client
    configured with the provided application settings.
    """
    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE,
        model=settings.OPENAI_MODEL_NAME,
        temperature=settings.TEMPERATURE,
    )

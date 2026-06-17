from functools import lru_cache
from fastapi import Depends
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from app.config import Settings
from app.graph.workflow import create_workflow
from app.services.llm import get_llm_client


@lru_cache
def get_settings() -> Settings:
    """
    Dependency to fetch loaded configuration settings.
    Uses lru_cache to load environment configuration once.
    """
    return Settings()


from fastapi import Header
from typing import Optional


def get_llm(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings)
) -> ChatOpenAI:
    """
    Dependency to obtain the LangChain OpenAI/compatible chat LLM model client.
    Prioritizes using the X-API-Key header if provided.
    """
    if x_api_key:
        return ChatOpenAI(
            api_key=x_api_key,
            base_url=settings.OPENAI_API_BASE,
            model=settings.OPENAI_MODEL_NAME,
            temperature=settings.TEMPERATURE,
        )
    return get_llm_client(settings)



# Global singleton instance of compiled workflow
_compiled_workflow: CompiledStateGraph = create_workflow()


def get_workflow() -> CompiledStateGraph:
    """
    Dependency to obtain the compiled LangGraph workflow instance.
    """
    return _compiled_workflow

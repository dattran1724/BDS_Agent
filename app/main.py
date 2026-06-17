import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.routes import router as agent_router
from app.dependencies import get_settings

# Configure logging format and level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("agent.main")

# Load environment configuration
load_dotenv(override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown lifecycle hooks.
    """
    logger.info("Initializing Real Estate AI Agent Backend...")
    # Validate settings on startup
    settings = get_settings()
    logger.info(
        f"Backend configured successfully. "
        f"Environment: '{settings.ENV}', API Port: {settings.PORT}"
    )
    yield
    logger.info("Shutting down Real Estate AI Agent Backend...")


app = FastAPI(
    title="Real Estate AI Agent Backend",
    description=(
        "Production-ready backend architecture for an AI Agent that writes "
        "Facebook content for real estate agents using LangGraph and FastAPI."
    ),
    version="0.1.0",
    lifespan=lifespan
)

# Set up CORS middleware for integration with frontend web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register workflow routes
app.include_router(agent_router)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health Check"])
async def health_check():
    """
    Endpoint verifying service availability and health status.
    """
    return {
        "status": "healthy",
        "service": "bds-agent-backend"
    }


if __name__ == "__main__":
    import uvicorn
    # Retrieve settings dynamically
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV == "development"
    )

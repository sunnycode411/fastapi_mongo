from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.services.db_service import init_db, close_db
from core.services.logger_service import request_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Initialize resources here
    await init_db()
    yield
    # Cleanup resources here
    await close_db()

app = FastAPI(lifespan=lifespan)

# Middleware definitions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set this to a list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Set this to a list of allowed HTTP methods
    allow_headers=["*"],  # Set this to a list of allowed headers
)
app.middleware("http")(request_logger)


if __name__ == "__main__":
    uvicorn.run("__main__:app", host="127.0.0.1", port=8000)

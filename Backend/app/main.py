import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings
from app.routers import webhook, review

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DevOpsPRAgent")

db_pool: AsyncConnectionPool | None = None
checkpointer: AsyncPostgresSaver | None = None

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle events:
    1. Initializes connection pool for PostgreSQL + pgvector with autocommit=True.
    2. Runs setup() on LangGraph AsyncPostgresSaver to ensure checkpoint tables exist.
    3. Gracefully closes connections on server shutdown.
    """
    global db_pool, checkpointer
    logger.info("Initializing application startup lifecycle...")

    try:
        logger.info(f"Connecting to PostgreSQL database at {settings.DATABASE_URL.split('@')[-1]}...")
        db_pool = AsyncConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=2,
            max_size=10,
            open=False,
            kwargs={"autocommit": True, "row_factory": dict_row}
        )
        await db_pool.open()
        await db_pool.wait()
        logger.info("Database connection pool established successfully.")

        checkpointer = AsyncPostgresSaver(db_pool)
        await checkpointer.setup()
        logger.info("LangGraph PostgreSQL Checkpoint tables verified/created successfully.")

        app.state.checkpointer = checkpointer
        app.state.db_pool = db_pool

        yield  

    except Exception as e:
        logger.critical(f"Fatal error during application startup: {str(e)}", exc_info=True)
        raise e
    finally:
        logger.info("Shutting down application... Closing database connection pool.")
        if db_pool:
            await db_pool.close()
            logger.info("Database connection pool closed.")


app = FastAPI(
    title="LangGraph Autonomous DevOps & PR Agent",
    description="Stateful Multi-Agent PR Review & DevOps automation engine with HITL & SSE streaming.",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(review.router)


@app.get("/", tags=["Health"])
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Simple health check endpoint to confirm API and database checkpointer readiness."""
    is_ready = hasattr(request.app.state, "checkpointer") and request.app.state.checkpointer is not None
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={
            "status": "online" if is_ready else "initializing",
            "service": "langgraph-autonomous-devops-pr-agent",
            "llm_model": settings.GROQ_MODEL,
            "checkpointer_ready": is_ready
        }
    )
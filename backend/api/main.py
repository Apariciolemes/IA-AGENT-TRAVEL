from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import uuid

from database.db import engine, Base
from api.routes import search, chat, booking

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Travel Agent API")
    # Create tables if they don't exist (in production use Alembic migrations)
    # Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down Travel Agent API")


app = FastAPI(
    title="Travel Agent API",
    description="API conversacional para busca de voos em dinheiro e milhas",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for trace ID
@app.middleware("http")
async def add_trace_id(request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response


# Include routers
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(booking.router, prefix="/api/v1", tags=["booking"])


@app.get("/")
async def root():
    return {
        "message": "Travel Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        trace_id=getattr(request.state, "trace_id", None)
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "trace_id": getattr(request.state, "trace_id", None)}
    )

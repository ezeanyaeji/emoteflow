from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.config import get_settings
from core.database import connect_db, close_db
from core.rate_limit import limiter
from routers import auth, emotion, suggestion, dashboard, admin, assignment
from services.emotion import load_model

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    load_model()  # Preload ONNX model to avoid cold-start latency
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time student emotion recognition and learning engagement platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(emotion.router, prefix="/api")
app.include_router(suggestion.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(assignment.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"status": "ok", "message": "Hello from FastAPI on Render!"}

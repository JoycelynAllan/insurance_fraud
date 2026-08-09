import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Resolve paths
app_dir = Path(__file__).resolve().parent
ml_dir = app_dir / "ml"
models_dir = ml_dir / "models"


# Programmatically add the 'ml' directory to sys.path to allow joblib/pickle
# to correctly resolve the pickled 'data_preprocessing' module namespace.
ml_path_str = str(ml_dir)
if ml_path_str not in sys.path:
    sys.path.insert(0, ml_path_str)

# Now safely import model definitions
from backend.app.ml import fraud_detection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize PostgreSQL tables and auto-migrate missing columns
    from backend.app.db import engine, Base, auto_migrate_schema
    import backend.app.models
    Base.metadata.create_all(bind=engine)
    auto_migrate_schema()

    # Seed database with synthetic agent data if tables are empty
    from backend.app.utils.seed_db import seed_if_empty
    await seed_if_empty()

    # Load ML models and components using joblib at startup
    app.state.isolation_forest = joblib.load(models_dir / "isolation_forest.pkl")
    app.state.xgboost_model = joblib.load(models_dir / "xgboost_model.pkl")
    app.state.preprocessor = joblib.load(models_dir / "preprocessor.pkl")
    
    # Pre-populate the global _model_instance in fraud_detection.py
    # to avoid double loading the models during inference
    model = fraud_detection.FraudDetectionModel()
    model.isolation_forest = app.state.isolation_forest
    model.xgboost_model = app.state.xgboost_model
    model.preprocessor = app.state.preprocessor
    model.is_trained = True
    fraud_detection._model_instance = model
    
    # Start the background scheduler
    from backend.app.services.scheduler import scheduler
    scheduler.start()
        
    yield
    # Shutdown logic
    scheduler.shutdown()

# Instantiate the FastAPI application
app = FastAPI(
    title="Micro-Insurance Fraud Detection API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
frontend_url = os.getenv("FRONTEND_URL")
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "https://insurance-fraud-4t3m.onrender.com",
    "https://frauddetection-three.vercel.app"
]
if frontend_url:
    clean_url = frontend_url.rstrip("/")
    if clean_url not in allowed_origins:
        allowed_origins.append(clean_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app|http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global CORS-preserving exception handlers
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"[GLOBAL EXCEPTION] {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Import and include routing
from fastapi.staticfiles import StaticFiles

# Mount static audio files for voice prompts
audio_dir = Path(__file__).resolve().parent / "voice" / "audio"
if audio_dir.exists():
    app.mount("/static/audio", StaticFiles(directory=str(audio_dir)), name="audio")

from backend.app.routes.analyze import router as analyze_router
from backend.app.routes.alerts import router as alerts_router
from backend.app.routes.agents import router as agents_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.voice import router as voice_router
from backend.app.routes.voice_callback import router as voice_callback_router
from backend.app.routes.otp import router as otp_router

app.include_router(analyze_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(voice_callback_router, prefix="/api")
app.include_router(otp_router, prefix="/api")
app.include_router(otp_router, prefix="/api/auth")

# Root health check route
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "fraud-detection-api"
    }

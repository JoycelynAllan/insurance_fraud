import sys
from pathlib import Path
from contextlib import asynccontextmanager
import pandas as pd
import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Resolve paths
app_dir = Path(__file__).resolve().parent
ml_dir = app_dir / "ml"
models_dir = ml_dir / "models"
backend_dir = app_dir.parent
csv_path = backend_dir / "data" / "synthetic" / "agent_transactions_features.csv"

# Programmatically add the 'ml' directory to sys.path to allow joblib/pickle
# to correctly resolve the pickled 'data_preprocessing' module namespace.
ml_path_str = str(ml_dir)
if ml_path_str not in sys.path:
    sys.path.insert(0, ml_path_str)

# Now safely import model definitions
from backend.app.ml import fraud_detection

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    
    # Load the agent features CSV into memory for fast querying
    if csv_path.exists():
        app.state.features_df = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"Features CSV not found at: {csv_path}")
        
    yield
    # Shutdown logic (none needed)

# Instantiate the FastAPI application
app = FastAPI(
    title="Micro-Insurance Fraud Detection API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routing
from backend.app.routes.analyze import router as analyze_router
app.include_router(analyze_router, prefix="/api")

# Root health check route
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "fraud-detection-api"
    }

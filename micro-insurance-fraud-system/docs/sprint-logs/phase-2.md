# Phase 2 Sprint Logs

## Week 4 — ML Models & Preprocessing
- Built the two-stage model pipeline (Isolation Forest + XGBoost).
- Designed the preprocessing steps including standard scaling.
- Generated synthetic transactions and saved them in features CSV.

## Week 5 — FastAPI Backend & REST Endpoints

### What was built
- Created the FastAPI entry point `backend/app/main.py`.
- Configured `CORSMiddleware` supporting wildcard origins, credentials, wildcard methods, and wildcard headers.
- Implemented startup lifespan context manager to load pickled models (`isolation_forest.pkl`, `xgboost_model.pkl`, and `preprocessor.pkl`) via `joblib` and store them in `app.state`.
- Read and cached the synthetic transaction features CSV (`agent_transactions_features.csv`) into the lifespan manager's `app.state` to enable performant, instant data querying.
- Implemented `/api/analyze` (POST) to score transactions in real time using Pydantic schema validation.
- Implemented `/api/agents/risk` (GET) to aggregate historical profiles for all 50 agents and return them sorted by their ML risk score.
- Implemented `/api/agents/{agent_id}/trend` (GET) to fetch and score the chronological history of transactions in the last 30 days for a specific agent.
- Created `backend/requirements.txt` containing all 16 required Python package dependencies.

### Flask → FastAPI conversion notes
- **Decorators**: Replaced Flask's global app decorator routing (`@app.route`) with modular router imports using FastAPI's `APIRouter` class.
- **Request Parsing**: Avoided Flask's unstructured `request.get_json()` by utilizing Pydantic's `BaseModel` schemas for strict type validation.
- **Startup Hooks**: Avoided the deprecated `@app.on_event("startup")` syntax in favor of the modern `lifespan` context manager, which handles initialization and cleanup using a single generator function.
- **Error Handling**: Replaced Flask's custom error handlers with FastAPI's `HTTPException` class, enabling cleaner exceptions and standard API structure.

### Problems hit
- **Pickle module resolution namespace issue**: `preprocessor.pkl` was saved under a scope expecting the `data_preprocessing` module to be present at the root of `sys.path`. When loaded in uvicorn from the root path, `joblib` failed with `ModuleNotFoundError: No module named 'data_preprocessing'`.
- **Request body vs query parameters validation**: Defining model properties cleanly in FastAPI routes required explicit model type-hinting, otherwise query/path parameters could be conflated with the JSON request body.
- **Model double-loading**: When using `score_transaction`, the function internally resolves and loads models on first call if the global variable `_model_instance` is `None`. This would cause the app to double-load model components into memory (once at startup and once on first route invocation).

### How they were solved
- Resolved the namespace issue by dynamically inserting the absolute `backend/app/ml/` folder path into `sys.path` using `pathlib` at the beginning of `main.py` and `routes/analyze.py`.
- Enforced input models with Pydantic (`AnalyzeRequest`) and typed path parameters (`agent_id: str`) in route definitions to leverage FastAPI's automatic serialization and validation.
- Avoided duplicate memory loading by pre-populating the global model instance `fraud_detection._model_instance` inside the lifespan context manager after loading the files via `joblib.load()`.

### Open items / tech debt
- Configure `allow_origins` dynamically in CORS middleware using an environment variable from a `.env` file instead of a hardcoded wildcard.
- Implement comprehensive unit tests for backend endpoints using FastAPI's `TestClient` and `pytest`.

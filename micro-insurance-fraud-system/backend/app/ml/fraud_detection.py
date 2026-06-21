import os
import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import xgboost as xgb
from joblib import dump, load
from pathlib import Path

# Try importing DataPreprocessor from the local directory
try:
    from data_preprocessing import DataPreprocessor
except ImportError:
    from backend.app.ml.data_preprocessing import DataPreprocessor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FraudDetectionModel:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.isolation_forest = None
        self.xgboost_model = None
        self.is_trained = False
        
        # Paths for saving models dynamically
        self.base_path = Path(__file__).parent.resolve()
        self.models_dir = self.base_path / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.if_model_path = self.models_dir / "isolation_forest.pkl"
        self.xgb_model_path = self.models_dir / "xgboost_model.pkl"
        self.preprocessor_path = self.models_dir / "preprocessor.pkl"

    def train(self, X, y, test_size=0.2, random_state=42):
        """
        Train the stacked two-stage fraud detection model.
        Stage 1: Isolation Forest (Unsupervised Anomaly Score)
        Stage 2: XGBoost Classifier (Supervised stacked on Isolation Forest features)
        """
        try:
            logger.info("Starting model training pipeline")
            
            # 1. Fit & Transform the preprocessor on the feature set
            X_processed = self.preprocessor.fit_transform(X)
            
            # 2. Train/Test Split (Stratified on target is_fraud)
            X_train, X_test, y_train, y_test = train_test_split(
                X_processed, y, test_size=test_size, random_state=random_state, stratify=y
            )
            
            # 3. Train Stage 1: Isolation Forest
            # Estimate contamination from training labels
            contamination = float(np.sum(y_train) / len(y_train))
            if contamination <= 0.0 or contamination >= 0.5:
                contamination = 0.05  # fallback default
                
            logger.info(f"Training Stage 1 (Isolation Forest) with contamination={contamination:.4f}")
            self.isolation_forest = IsolationForest(
                n_estimators=100,
                contamination=contamination,
                random_state=random_state
            )
            self.isolation_forest.fit(X_train)
            
            # 4. Generate stacked features for XGBoost stage
            X_train_xgb = X_train.copy()
            X_train_xgb['anomaly_score'] = self.isolation_forest.decision_function(X_train)
            X_train_xgb['anomaly_pred'] = np.where(self.isolation_forest.predict(X_train) == -1, 1, 0)
            
            # 5. Train Stage 2: XGBoost Classifier
            logger.info("Training Stage 2 (XGBoost Classifier)")
            self.xgboost_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=random_state,
                eval_metric='logloss'
            )
            self.xgboost_model.fit(X_train_xgb, y_train)
            
            # 6. Generate stacked features for the evaluation dataset
            X_test_xgb = X_test.copy()
            X_test_xgb['anomaly_score'] = self.isolation_forest.decision_function(X_test)
            X_test_xgb['anomaly_pred'] = np.where(self.isolation_forest.predict(X_test) == -1, 1, 0)
            
            # 7. Make predictions and evaluate performance
            y_pred = self.xgboost_model.predict(X_test_xgb)
            metrics = self.evaluate(y_test, y_pred)
            
            # 8. Persist the models to disk
            self.save_model()
            self.is_trained = True
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error during training pipeline: {str(e)}")
            raise

    def predict(self, X):
        """
        Make predictions using the trained two-stage model.
        """
        try:
            if not self.is_trained:
                raise ValueError("Model is not trained. Train or load a model first.")
                
            X_processed = self.preprocessor.transform(X)
            
            # Generate Isolation Forest features
            X_xgb = X_processed.copy()
            X_xgb['anomaly_score'] = self.isolation_forest.decision_function(X_processed)
            X_xgb['anomaly_pred'] = np.where(self.isolation_forest.predict(X_processed) == -1, 1, 0)
            
            return self.xgboost_model.predict(X_xgb)
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise

    def evaluate(self, y_true, y_pred):
        """
        Print and return evaluation metrics.
        """
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred)
        
        print("\n=== Model Evaluation Results ===")
        print(f"Accuracy: {acc:.4f}")
        print(f"Precision: {prec:.4f}")
        print(f"Recall: {rec:.4f}")
        print(f"F1 score: {f1:.4f}")
        print("Confusion Matrix:")
        print(cm)
        print("================================")
        
        return {
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1_score': f1,
            'confusion_matrix': cm.tolist()
        }

    def save_model(self):
        """
        Save the model components via joblib.
        """
        try:
            logger.info(f"Saving models to {self.models_dir}")
            dump(self.isolation_forest, str(self.if_model_path))
            dump(self.xgboost_model, str(self.xgb_model_path))
            dump(self.preprocessor, str(self.preprocessor_path))
            logger.info("Models saved successfully.")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise

    def load_model(self):
        """
        Load model components from disk.
        """
        try:
            logger.info(f"Loading models from {self.models_dir}")
            if not self.if_model_path.exists() or not self.xgb_model_path.exists():
                raise FileNotFoundError("Model files do not exist. Please train the model first.")
                
            self.isolation_forest = load(str(self.if_model_path))
            self.xgboost_model = load(str(self.xgb_model_path))
            self.preprocessor = load(str(self.preprocessor_path))
            self.is_trained = True
            logger.info("Models loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

# Global variable to cache the model instance
_model_instance = None

def get_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = FraudDetectionModel()
        _model_instance.load_model()
    return _model_instance

def score_transaction(data: dict) -> dict:
    """
    Score a single transaction.
    
    Parameters:
    -----------
    data : dict
        Dict containing keys: 'remittance_delay_hours', 'cash_ratio', 
        'deviation_from_agent_mean', 'missed_consecutive_count', 'amount'
        
    Returns:
    --------
    dict
        {
            "risk_score": float,   # 0-100
            "is_fraud": bool,
            "flag_reason": str
        }
    """
    # 1. Get cached trained model
    model = get_model()
    
    # 2. Convert dictionary input to DataFrame
    df = pd.DataFrame([data])
    
    # 3. Transform inputs using the preprocessor
    X_processed = model.preprocessor.transform(df)
    
    # 4. Generate first stage features (Isolation Forest output)
    anomaly_score = model.isolation_forest.decision_function(X_processed)[0]
    anomaly_pred = 1 if model.isolation_forest.predict(X_processed)[0] == -1 else 0
    
    # 5. Build stacked feature set for XGBoost classifier
    X_xgb = X_processed.copy()
    X_xgb['anomaly_score'] = anomaly_score
    X_xgb['anomaly_pred'] = anomaly_pred
    
    # 6. Generate prediction probability with XGBoost (probability of class 1 / fraud)
    xgb_prob = model.xgboost_model.predict_proba(X_xgb)[0][1]
    
    # 7. Scale risk score to 0-100
    risk_score = float(xgb_prob * 100)
    
    # 8. Determine boolean is_fraud threshold on risk_score (threshold >= 50.0)
    is_fraud = bool(risk_score >= 50.0)
    
    # 9. Dynamic flag reasoning based on dominant features
    reasons = []
    rem_delay = data.get('remittance_delay_hours', 0)
    cash_ratio = data.get('cash_ratio', 0)
    missed_count = data.get('missed_consecutive_count', 0)
    deviation = data.get('deviation_from_agent_mean', 0)
    
    if rem_delay > 168:
        reasons.append(f"High remittance delay ({rem_delay}h)")
    if cash_ratio > 0.6:
        reasons.append(f"High cash ratio ({cash_ratio:.2f})")
    if missed_count > 2:
        reasons.append(f"Consecutive missed remittances ({missed_count})")
    if deviation > 500:
        reasons.append(f"Large positive deviation from agent mean ({deviation:+.2f})")
        
    if is_fraud:
        if reasons:
            flag_reason = "Flagged due to: " + " and ".join(reasons)
        else:
            flag_reason = f"Combined model indicates high risk (xgb probability: {xgb_prob:.2f})"
    else:
        flag_reason = "Transaction verified as low risk"
        
    return {
        "risk_score": round(risk_score, 2),
        "is_fraud": is_fraud,
        "flag_reason": flag_reason
    }

if __name__ == "__main__":
    # Resolve path dynamically for loading synthetic data
    script_dir = Path(__file__).parent.resolve()
    
    # Look for agent_transactions_features.csv in parent paths
    data_paths = [
        script_dir.parent.parent.parent / "data" / "synthetic" / "agent_transactions_features.csv",
        script_dir.parent.parent / "data" / "synthetic" / "agent_transactions_features.csv",
        script_dir / "data" / "synthetic" / "agent_transactions_features.csv"
    ]
    
    data_path = None
    for p in data_paths:
        if p.exists():
            data_path = p
            break
            
    if data_path is None:
        raise FileNotFoundError("Could not find agent_transactions_features.csv in expected paths.")
        
    print(f"Loading synthetic data from: {data_path}")
    df = pd.read_csv(data_path)
    
    # Target and feature set
    feature_cols = ['remittance_delay_hours', 'cash_ratio', 'deviation_from_agent_mean', 'missed_consecutive_count', 'amount']
    X = df[feature_cols]
    y = df['is_fraud']
    
    # Initialize and train model
    model = FraudDetectionModel()
    metrics = model.train(X, y)
    
    # Verify score_transaction on a mock transaction
    test_dict = {
        'remittance_delay_hours': 240,
        'cash_ratio': 0.82,
        'deviation_from_agent_mean': 150.0,
        'missed_consecutive_count': 3,
        'amount': 500.0
    }
    
    print("\nVerifying score_transaction function output:")
    result = score_transaction(test_dict)
    print(result)

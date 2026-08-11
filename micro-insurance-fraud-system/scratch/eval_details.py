import sys
from pathlib import Path
ml_dir = Path(__file__).resolve().parent.parent / "backend" / "app" / "ml"
if str(ml_dir) not in sys.path:
    sys.path.insert(0, str(ml_dir))

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, classification_report
from backend.app.ml.fraud_detection import FraudDetectionModel

data_path = Path(__file__).resolve().parent.parent / "backend" / "data" / "synthetic" / "agent_transactions_features.csv"
df = pd.read_csv(data_path)

feature_cols = ['remittance_delay_hours', 'cash_ratio', 'deviation_from_agent_mean', 'missed_consecutive_count', 'amount']
X = df[feature_cols]
y = df['is_fraud']

model = FraudDetectionModel()
model.load_model()

X_processed = model.preprocessor.transform(X)
X_xgb = X_processed.copy()
X_xgb['anomaly_score'] = model.isolation_forest.decision_function(X_processed)
X_xgb['anomaly_pred'] = np.where(model.isolation_forest.predict(X_processed) == -1, 1, 0)

probs = model.xgboost_model.predict_proba(X_xgb)[:, 1]
preds = model.xgboost_model.predict(X_xgb)
auc = roc_auc_score(y, probs)

importances = model.xgboost_model.feature_importances_
feature_names = list(X_xgb.columns)

print(f"Overall Dataset Size: {len(df)} transactions")
print(f"Fraud Class Distribution: Non-Fraud={sum(y==0)}, Fraud={sum(y==1)} ({sum(y==1)/len(y)*100:.2f}%)")
print(f"ROC-AUC Score: {auc:.4f}")
print("Feature Importances:")
for name, imp in zip(feature_names, importances):
    print(f"  - {name}: {imp*100:.2f}%")

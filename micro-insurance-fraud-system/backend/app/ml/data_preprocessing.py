import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class DataPreprocessor:
    def __init__(self):
        # Target features for model training and prediction
        self.numeric_features = [
            'remittance_delay_hours', 
            'cash_ratio', 
            'deviation_from_agent_mean', 
            'missed_consecutive_count', 
            'amount'
        ]
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def fit(self, X):
        """
        Fit the standard scaler to the feature data.
        """
        try:
            logger.info("Fitting preprocessing pipeline")
            # Select target features and fit standard scaler
            self.scaler.fit(X[self.numeric_features])
            self.is_fitted = True
            logger.info("Preprocessing pipeline fitted successfully")
            return self
        except Exception as e:
            logger.error(f"Error fitting preprocessing pipeline: {str(e)}")
            raise
            
    def transform(self, X):
        """
        Transform features using the fitted standard scaler.
        """
        try:
            if not self.is_fitted:
                raise ValueError("Preprocessor has not been fitted yet. Call fit() first.")
            logger.info("Transforming data using preprocessing pipeline")
            # Extract features, scale them, and preserve index and column names
            X_scaled = self.scaler.transform(X[self.numeric_features])
            X_transformed = pd.DataFrame(
                X_scaled, 
                columns=self.numeric_features, 
                index=X.index
            )
            logger.info(f"Data transformed successfully. Shape: {X_transformed.shape}")
            return X_transformed
        except Exception as e:
            logger.error(f"Error transforming data: {str(e)}")
            raise
            
    def fit_transform(self, X):
        """
        Fit the preprocessing pipeline and transform the data
        """
        self.fit(X)
        return self.transform(X)
        
    def preprocess_data(self, df):
        """
        Complete preprocessing workflow. Fits standard scaler on the fly 
        during training, and uses already fitted scaler during prediction.
        """
        if not self.is_fitted:
            return self.fit_transform(df)
        else:
            return self.transform(df)

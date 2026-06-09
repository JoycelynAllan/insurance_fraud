import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import logging

logger = logging.getLogger(__name__)

class DataPreprocessor:
    def __init__(self):
        self.numeric_features = ['amount']
        self.categorical_features = ['merchant_category', 'location']
        self.time_features = ['timestamp']
        self.preprocessor = None
        
    def fit(self, X):
        """
        Fit the preprocessing pipeline to the training data
        """
        try:
            logger.info("Fitting preprocessing pipeline")
            
            # Numeric features pipeline
            numeric_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ])
            
            # Categorical features pipeline
            categorical_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
                ('onehot', OneHotEncoder(handle_unknown='ignore'))
            ])
            
            # Combine all transformers
            self.preprocessor = ColumnTransformer(
                transformers=[
                    ('num', numeric_transformer, self.numeric_features),
                    ('cat', categorical_transformer, self.categorical_features)
                ],
                remainder='drop'  # Drop other columns not specified
            )
            
            # Fit the preprocessor to the data
            self.preprocessor.fit(X)
            logger.info("Preprocessing pipeline fitted successfully")
            return self
            
        except Exception as e:
            logger.error(f"Error fitting preprocessing pipeline: {str(e)}")
            raise
    
    def transform(self, X):
        """
        Transform data using the fitted preprocessing pipeline
        """
        try:
            if self.preprocessor is None:
                raise ValueError("Preprocessor has not been fitted yet. Call fit() first.")
            
            logger.info("Transforming data using preprocessing pipeline")
            X_transformed = self.preprocessor.transform(X)
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
    
    def extract_time_features(self, df):
        """
        Extract features from timestamp column
        """
        try:
            logger.info("Extracting time features")
            
            # Make a copy to avoid modifying the original
            df_copy = df.copy()
            
            # Convert timestamp to datetime if it's not already
            if 'timestamp' in df_copy.columns:
                if not pd.api.types.is_datetime64_any_dtype(df_copy['timestamp']):
                    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
                
                # Extract time-based features
                df_copy['hour'] = df_copy['timestamp'].dt.hour
                df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek
                df_copy['day_of_month'] = df_copy['timestamp'].dt.day
                df_copy['month'] = df_copy['timestamp'].dt.month
                df_copy['year'] = df_copy['timestamp'].dt.year
                df_copy['is_weekend'] = df_copy['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
            
            logger.info("Time features extracted successfully")
            return df_copy
            
        except Exception as e:
            logger.error(f"Error extracting time features: {str(e)}")
            raise
    
    def preprocess_data(self, df):
        """
        Complete preprocessing workflow for transaction data
        """
        try:
            logger.info("Starting complete preprocessing workflow")
            
            # Make a copy to avoid modifying the original
            df_copy = df.copy()
            
            # Extract time features
            df_copy = self.extract_time_features(df_copy)
            
            # Handle missing values for key fields
            df_copy['merchant'] = df_copy['merchant'].fillna('unknown')
            df_copy['merchant_category'] = df_copy['merchant_category'].fillna('unknown')
            df_copy['location'] = df_copy['location'].fillna('unknown')
            
            # Apply transformations
            numeric_cols = self.numeric_features + ['hour', 'day_of_week', 'day_of_month', 'month', 'year', 'is_weekend']
            df_numeric = df_copy[numeric_cols].copy()
            
            # Scale numeric features
            scaler = StandardScaler()
            df_copy[numeric_cols] = scaler.fit_transform(df_numeric)
            
            # One-hot encode categorical features if needed
            categorical_cols = self.categorical_features
            for col in categorical_cols:
                if col in df_copy.columns:
                    dummies = pd.get_dummies(df_copy[col], prefix=col, drop_first=True)
                    df_copy = pd.concat([df_copy, dummies], axis=1)
            
            logger.info("Complete preprocessing workflow finished successfully")
            return df_copy
            
        except Exception as e:
            logger.error(f"Error in complete preprocessing workflow: {str(e)}")
            raise

import os
import numpy as np
import pandas as pd
import pickle
import logging
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from data_preprocessing import DataPreprocessor
from joblib import dump, load

logger = logging.getLogger(__name__)

class FraudDetectionModel:
    def __init__(self, model_type='random_forest'):
        self.model_type = model_type
        self.model = None
        self.preprocessor = DataPreprocessor()
        self.model_path = f'./models/{model_type}_model.joblib'
        self.is_trained = False
        
        # Create models directory if it doesn't exist
        os.makedirs('./models', exist_ok=True)
    
    def train(self, X, y, test_size=0.2, random_state=42):
        """
        Train the fraud detection model
        
        Parameters:
        -----------
        X : pandas.DataFrame
            The feature data
        y : pandas.Series
            The target variable (fraud or not)
        test_size : float
            Proportion of data to use for testing
        random_state : int
            Random seed for reproducibility
        """
        try:
            logger.info(f"Training {self.model_type} model")
            
            # Preprocess the data
            X_processed = self.preprocessor.preprocess_data(X)
            
            # Split the data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(
                X_processed, y, test_size=test_size, random_state=random_state, stratify=y
            )
            
            # Initialize and train the model based on model_type
            if self.model_type == 'random_forest':
                # Define the model
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=None,
                    min_samples_split=2,
                    min_samples_leaf=1,
                    random_state=random_state,
                    class_weight='balanced'
                )
                
                # Train the model
                self.model.fit(X_train, y_train)
                
            elif self.model_type == 'isolation_forest':
                # For anomaly detection
                self.model = IsolationForest(
                    n_estimators=100,
                    contamination=float(sum(y) / len(y)),  # Estimated contamination ratio
                    random_state=random_state
                )
                
                # Train the model
                self.model.fit(X_train)
                
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
            
            # Evaluate the model
            y_pred = self.predict(X_test)
            
            # Calculate metrics
            metrics = self.evaluate(y_test, y_pred)
            
            # Save the trained model
            self.save_model()
            
            self.is_trained = True
            logger.info(f"Model training completed. Metrics: {metrics}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    def predict(self, X):
        """
        Make predictions using the trained model
        
        Parameters:
        -----------
        X : pandas.DataFrame
            The feature data
        
        Returns:
        --------
        numpy.ndarray
            Predicted classes or anomaly scores
        """
        try:
            if self.model is None:
                raise ValueError("Model not trained. Call train() first or load a saved model.")
            
            logger.info("Making predictions")
            
            # Preprocess the data
            X_processed = self.preprocessor.preprocess_data(X)
            
            # Make predictions based on model type
            if self.model_type == 'random_forest':
                y_pred = self.model.predict(X_processed)
            
            elif self.model_type == 'isolation_forest':
                # Convert isolation forest predictions to 0 and 1
                # Isolation forest returns -1 for anomalies and 1 for normal
                raw_pred = self.model.predict(X_processed)
                y_pred = np.where(raw_pred == -1, 1, 0)  # 1 for fraud (anomaly), 0 for normal
                
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
            
            logger.info("Predictions completed")
            return y_pred
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise
    
    def predict_proba(self, X):
        """
        Get probability scores for predictions
        
        Parameters:
        -----------
        X : pandas.DataFrame
            The feature data
        
        Returns:
        --------
        numpy.ndarray
            Probability scores
        """
        try:
            if self.model is None:
                raise ValueError("Model not trained. Call train() first or load a saved model.")
            
            logger.info("Getting prediction probabilities")
            
            # Preprocess the data
            X_processed = self.preprocessor.preprocess_data(X)
            
            # Get probabilities based on model type
            if self.model_type == 'random_forest':
                # Get the probability of the positive class (fraud)
                probas = self.model.predict_proba(X_processed)[:, 1]
                
            elif self.model_type == 'isolation_forest':
                # Isolation forest doesn't have predict_proba
                # We can convert decision_function to a pseudo-probability
                decision_scores = self.model.decision_function(X_processed)
                # Convert to the range [0, 1] where higher values indicate anomalies (fraud)
                # Lower decision_function values indicate anomalies in isolation forest
                probas = 1 - (1 / (1 + np.exp(-decision_scores)))
                
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
            
            logger.info("Prediction probabilities calculated")
            return probas
            
        except Exception as e:
            logger.error(f"Error getting prediction probabilities: {str(e)}")
            raise
    
    def evaluate(self, y_true, y_pred):
        """
        Evaluate the model performance
        
        Parameters:
        -----------
        y_true : array-like
            True labels
        y_pred : array-like
            Predicted labels
        
        Returns:
        --------
        dict
            Dictionary containing evaluation metrics
        """
        try:
            logger.info("Evaluating model performance")
            
            # Calculate metrics
            acc = accuracy_score(y_true, y_pred)
            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            conf_matrix = confusion_matrix(y_true, y_pred)
            
            # Create metrics dictionary
            metrics = {
                'accuracy': acc,
                'precision': prec,
                'recall': rec,
                'f1_score': f1,
                'confusion_matrix': conf_matrix.tolist()
            }
            
            logger.info(f"Model evaluation completed: Accuracy={acc:.4f}, Precision={prec:.4f}, Recall={rec:.4f}, F1={f1:.4f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise
    
    def save_model(self):
        """
        Save the trained model to disk
        """
        try:
            if self.model is None:
                raise ValueError("No model to save. Train a model first.")
            
            logger.info(f"Saving model to {self.model_path}")
            
            # Save the model using joblib
            dump(self.model, self.model_path)
            
            # Save the preprocessor as well
            preprocessor_path = self.model_path.replace('_model.joblib', '_preprocessor.joblib')
            dump(self.preprocessor, preprocessor_path)
            
            logger.info("Model saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self):
        """
        Load a trained model from disk
        """
        try:
            model_path = self.model_path
            preprocessor_path = self.model_path.replace('_model.joblib', '_preprocessor.joblib')
            
            logger.info(f"Loading model from {model_path}")
            
            # Check if model file exists
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            # Load the model
            self.model = load(model_path)
            
            # Load the preprocessor if it exists
            if os.path.exists(preprocessor_path):
                self.preprocessor = load(preprocessor_path)
            
            self.is_trained = True
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

import joblib
import os

model_path = 'model/logistic_regression_model.pkl'
scaler_path = 'model/feature_scaler.pkl'

try:
    scaler = joblib.load(scaler_path)
    model = joblib.load(model_path)
    
    print(f"Scaler expects: {scaler.n_features_in_} features")
    if hasattr(model, 'n_features_in_'):
        print(f"Model expects: {model.n_features_in_} features")
    else:
        print(f"Model coefficients shape: {model.coef_.shape}")
        
except Exception as e:
    print(f"Error: {e}")

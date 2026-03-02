import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os

# 1. Generate Synthetic Data based on PDF rules
np.random.seed(42)
n_samples = 1000

data = {
    'sleep_hours': np.random.uniform(4, 10, n_samples),
    'study_hours': np.random.uniform(0, 8, n_samples),
    'workout_minutes': np.random.uniform(0, 120, n_samples),
    'journal_minutes': np.random.uniform(0, 60, n_samples),
    'reading_minutes': np.random.uniform(0, 60, n_samples),
    'mood': np.random.randint(1, 6, n_samples)
}

df = pd.DataFrame(data)

# Calculate routine strength (Weights from PDF)
norms = {
    'sleep': df['sleep_hours'] / 8.0,
    'study': df['study_hours'] / 5.0,
    'workout': df['workout_minutes'] / 60.0,
    'journal': df['journal_minutes'] / 30.0,
    'reading': df['reading_minutes'] / 60.0,
    'mood': df['mood'] / 5.0
}

routine_strength = (
    0.25 * norms['sleep'] +
    0.25 * norms['study'] +
    0.20 * norms['mood'] +
    0.10 * norms['workout'] +
    0.10 * norms['reading'] +
    0.10 * norms['journal']
)

# Target: p_slip = 1 if routine_strength is low
# Add some noise to make it realistic
p_slip_prob = 1.0 - routine_strength
df['p_slip'] = (p_slip_prob > 0.6).astype(int)

# 2. Train Model
X = df[['sleep_hours', 'study_hours', 'workout_minutes', 'journal_minutes', 'reading_minutes', 'mood']]
y = df['p_slip']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression()
model.fit(X_scaled, y)

# 3. Save New Models
os.makedirs('model', exist_ok=True)
joblib.dump(model, 'model/logistic_regression_model.pkl')
joblib.dump(scaler, 'model/feature_scaler.pkl')

print("Success: Retrained model with 6 features.")
print(f"New Scaler expects: {scaler.n_features_in_} features")

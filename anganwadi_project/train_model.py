import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

# Sample training data (in real use, you'd use a larger dataset)
# Features: weight_change, attendance_percent, age_months
# Label: risk_level (0=Safe, 1=Moderate, 2=High Risk)

data = {
    'weight_change': [0.5, -0.3, -0.8, -1.0, 0.2, -0.5, 0.8, -1.2, 0.1, -0.9,
                       0.6, -0.2, -1.5, 0.3, -0.7, 0.9, -1.1, 0.4, -0.4, -1.3],
    'attendance_percent': [95, 70, 50, 40, 90, 65, 98, 35, 88, 45,
                            96, 75, 30, 92, 55, 97, 38, 89, 68, 33],
    'age_months': [24, 30, 18, 12, 36, 20, 48, 15, 28, 22,
                   40, 26, 10, 33, 19, 44, 14, 31, 23, 16],
    'risk_level': [0, 1, 2, 2, 0, 1, 0, 2, 0, 2,
                   0, 1, 2, 0, 1, 0, 2, 0, 1, 2]
}

df = pd.DataFrame(data)

X = df[['weight_change', 'attendance_percent', 'age_months']]
y = df['risk_level']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, 'model/risk_model.pkl')
print("✅ Model trained and saved successfully!")
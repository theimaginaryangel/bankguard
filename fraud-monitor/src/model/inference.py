try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

import os

# We load the AI's "brain" into memory as soon as this file is imported.
# In AWS Lambda, this happens during the "cold start", saving time on future runs!
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
FEATURES_PATH = os.path.join(os.path.dirname(__file__), "feature_names.joblib")

_model = None
_feature_names = None

def load_ai():
    global _model, _feature_names
    if not HAS_JOBLIB or not HAS_NUMPY:
        print("joblib or numpy not installed, gracefully degrading to rules engine.")
        return
    if _model is None:
        try:
            _model = joblib.load(MODEL_PATH)
            _feature_names = joblib.load(FEATURES_PATH)
        except Exception as e:
            print(f"Failed to load AI model. Did you run train.py? Error: {e}")

def score_transaction(transaction):
    """
    Takes a single transaction dictionary and asks the AI: "Is this weird?"
    
    Returns:
        risk_score: A number between 0 and 1. Closer to 1 = more likely to be fraud.
        contributing_features: A dictionary explaining WHICH features were weirdest.
    """
    load_ai()
    if not _model:
        return 0.0, {}

    # 1. Extract only the features the AI was trained on (V1-V28, Amount)
    input_data = []
    for feature in _feature_names:
        # Default to 0 if the data is missing
        val = float(transaction.get(feature, 0.0))
        input_data.append(val)
        
    # IsolationForest expects a 2D array (a list of lists)
    X = np.array([input_data])
    
    # 2. Get the anomaly score
    # score_samples returns a negative number. Lower (more negative) = more anomalous.
    # We convert it to a positive "risk score" between 0 and 1 to make it easy for humans.
    raw_score = _model.score_samples(X)[0]
    
    # A simple conversion trick: raw scores usually range from -0.3 to -0.85.
    # We want -0.4 to be 0.0 (normal) and -0.75+ to be 1.0 (fraud).
    # risk_score = (abs(raw_score) - 0.4) / (0.75 - 0.4)
    risk_score = min(max((abs(raw_score) - 0.4) / 0.35, 0.0), 1.0)
    
    # 3. Explainability (The "Why?")
    # A recruiter or auditor will ask: "Why did the AI flag this?"
    # Since Isolation Forest doesn't easily tell us this natively, we use a simple heuristic:
    # Which of the transaction's features are furthest from 0? (In PCA data, 0 is the average)
    contributing_features = {}
    if risk_score > 0.5:
        # Pair up the feature names with their absolute values
        feature_importance = [(name, abs(val)) for name, val in zip(_feature_names, input_data)]
        # Sort them so the biggest numbers (most unusual) are first
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        # Keep the top 3 biggest reasons
        for name, val in feature_importance[:3]:
            contributing_features[name] = val
            
    return risk_score, contributing_features

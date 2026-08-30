import os

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

# Primary path in /tmp (if dynamically retrained), fallback to package bundle
TMP_MODEL_PATH = "/tmp/model.joblib"
TMP_FEATURES_PATH = "/tmp/feature_names.joblib"
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
DEFAULT_FEATURES_PATH = os.path.join(os.path.dirname(__file__), "feature_names.joblib")

_model = None
_feature_names = None
_load_attempted = False

def load_ai(force_reload=False):
    global _model, _feature_names, _load_attempted
    if not HAS_JOBLIB or not HAS_NUMPY:
        if not _load_attempted:
            print("joblib or numpy not installed, gracefully degrading to rules engine.")
            _load_attempted = True
        return
        
    if _model is not None and not force_reload:
        return

    _load_attempted = True
    
    # Try /tmp first (freshly retrained), then package bundle
    model_path = TMP_MODEL_PATH if os.path.exists(TMP_MODEL_PATH) else DEFAULT_MODEL_PATH
    features_path = TMP_FEATURES_PATH if os.path.exists(TMP_FEATURES_PATH) else DEFAULT_FEATURES_PATH

    if os.path.exists(model_path) and os.path.exists(features_path):
        try:
            _model = joblib.load(model_path)
            _feature_names = joblib.load(features_path)
            print(f"Loaded AI model successfully from {model_path} ({len(_feature_names)} features).")
        except Exception as e:
            print(f"Failed to load AI model from {model_path}: {e}")
            _model = None
            _feature_names = None
    else:
        print(f"Model file not found at {model_path} or {features_path}.")

def retrain_model(transactions):
    """
    Dynamically retrains the Isolation Forest model on the newly uploaded batch data.
    Saves the new model to /tmp/ and hot-reloads it in memory.
    """
    global _model, _feature_names
    if not HAS_JOBLIB or not HAS_NUMPY:
        print("Cannot retrain model: joblib or numpy missing.")
        return False
        
    if not transactions or len(transactions) < 5:
        print("Not enough transactions in batch to retrain AI model (minimum 5 required).")
        return False

    try:
        from sklearn.ensemble import IsolationForest
        
        # 1. Identify ML features present in the transactions
        first_row = transactions[0]
        pca_features = [f"V{i}" for i in range(1, 29) if f"V{i}" in first_row]
        
        if not pca_features:
            print("Batch has no PCA features (V1-V28). Skipping dynamic ML retraining.")
            return False

        feature_cols = pca_features + (["Amount"] if "Amount" in first_row or "transaction_dollar_amount" in first_row else [])
        
        # 2. Build training matrix X
        X_list = []
        for row in transactions:
            row_vals = []
            for feat in feature_cols:
                raw_val = row.get(feat)
                if feat == "Amount" and raw_val is None:
                    raw_val = row.get("transaction_dollar_amount")
                try:
                    val = float(raw_val or 0.0)
                except (ValueError, TypeError):
                    val = 0.0
                row_vals.append(val)
            X_list.append(row_vals)

        X = np.array(X_list)
        if X.shape[0] < 5 or X.shape[1] < 1:
            return False

        # 3. Fit new IsolationForest on the uploaded dataset
        print(f"Retraining Isolation Forest on {X.shape[0]} rows and {X.shape[1]} features...")
        new_model = IsolationForest(contamination=0.02, random_state=42)
        new_model.fit(X)

        # 4. Save to /tmp/
        try:
            joblib.dump(new_model, TMP_MODEL_PATH)
            joblib.dump(feature_cols, TMP_FEATURES_PATH)
        except Exception as e:
            print(f"Could not persist model to /tmp: {e}")

        # 5. Hot-reload model into memory
        _model = new_model
        _feature_names = feature_cols
        print("Dynamic ML retraining complete and model hot-reloaded!")
        return True
    except Exception as e:
        print(f"Error during dynamic ML retraining: {e}")
        return False

def score_transaction(transaction):
    """
    Takes a single transaction dictionary and asks the AI: 'Is this weird?'
    
    Returns:
        risk_score: A float between 0.0 and 1.0.
        contributing_features: A dictionary of the top unusual features.
    """
    load_ai()
    if _model is None or not _feature_names:
        return 0.0, {}

    try:
        input_data = []
        for feature in _feature_names:
            raw_val = transaction.get(feature)
            if feature == "Amount" and raw_val is None:
                raw_val = transaction.get("transaction_dollar_amount")
            try:
                val = float(raw_val or 0.0)
            except (ValueError, TypeError):
                val = 0.0
            input_data.append(val)

        X = np.array([input_data])
        raw_score = _model.score_samples(X)[0]

        # Convert score_samples (-0.3 to -0.85 typical) to 0.0 - 1.0 risk score
        risk_score = min(max((abs(raw_score) - 0.4) / 0.35, 0.0), 1.0)
        risk_score = round(float(risk_score), 4)

        contributing_features = {}
        if risk_score >= 0.4:
            feature_importance = []
            for name, val in zip(_feature_names, input_data):
                # Scale Amount deviation relative to PCA magnitude for explainability
                deviation = abs(val) / 100.0 if name == "Amount" else abs(val)
                feature_importance.append((name, val, deviation))
                
            feature_importance.sort(key=lambda x: x[2], reverse=True)
            for name, val, _ in feature_importance[:3]:
                contributing_features[name] = round(float(val), 2)

        return risk_score, contributing_features
    except Exception as e:
        print(f"Error scoring transaction: {e}")
        return 0.0, {}

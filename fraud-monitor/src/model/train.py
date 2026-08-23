import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os

def train_model(csv_file="creditcard_augmented.csv"):
    """
    This script teaches our AI (an Isolation Forest) what "normal" transactions look like.
    
    Why Isolation Forest?
    Imagine a forest full of trees. Normal trees look alike and clump together. 
    A weird, strange tree (an anomaly) stands out and is easy to isolate. 
    This algorithm works the same way: it isolates data points. If a data point 
    is easy to isolate, it's considered an anomaly (fraud!).
    """
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please run prep_data.py first!")
        return

    print("1. Loading our transaction data...")
    df = pd.read_csv(csv_file)
    
    # We only want to train our AI on the features (V1 through V28, and Amount).
    # We drop the fake columns we made for the rules engine, and the 'Class' column
    # because Isolation Forest is "unsupervised" (it learns without being told what's fraud).
    features_to_drop = ['Class', 'Time', 'accountId', 'merchantCategory', 'recentTransactionsCount']
    X = df.drop(columns=[col for col in features_to_drop if col in df.columns])
    
    print("2. Training the Isolation Forest AI...")
    # contamination=0.01 means we expect roughly 1% of the data to be fraudulent
    # random_state=42 just ensures we get the same results if we run it twice
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(X)
    
    print("3. Saving the trained AI's 'brain' to model.joblib...")
    # We save the model into a file so our Lambda function can load it later without retraining!
    joblib.dump(model, "model.joblib")
    
    # We also save the feature names so the Lambda knows exactly what columns to look for
    feature_names = X.columns.tolist()
    joblib.dump(feature_names, "feature_names.joblib")
    
    print("Done! The AI is trained and ready.")

if __name__ == "__main__":
    train_model()

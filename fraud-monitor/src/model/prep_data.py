import pandas as pd
import random
import os

def prepare_synthetic_data(input_csv="creditcard.csv", output_csv="creditcard_augmented.csv"):
    """
    The Kaggle Credit Card Fraud dataset is great, but it's completely anonymized.
    It only gives us numbers (V1, V2, etc.), Time, Amount, and Class (Fraud or Not).
    
    To build realistic rules (like checking merchant categories or account velocity),
    we need to INVENT that data and add it to our CSV. That's what this script does!
    """
    
    if not os.path.exists(input_csv):
        print(f"Oops! I couldn't find {input_csv}.")
        print("Please download it from Kaggle and place it in this folder.")
        return
        
    print(f"Loading {input_csv}... this might take a second because it's a big file!")
    df = pd.read_csv(input_csv)
    
    print("Adding fake Account IDs...")
    # Give every transaction a random account ID from 1 to 1000
    df['accountId'] = [f"acc_{random.randint(1, 1000)}" for _ in range(len(df))]
    
    print("Adding fake Merchant Categories...")
    # Randomly assign merchants, but make the 'high risk' ones less common.
    merchants = ['groceries', 'gas_station', 'restaurant', 'online_retail', 'crypto_exchange', 'jewelry']
    weights = [0.3, 0.2, 0.2, 0.2, 0.05, 0.05] 
    df['merchantCategory'] = random.choices(merchants, weights=weights, k=len(df))
    
    print("Adding fake Recent Transactions Count (Velocity)...")
    # Random number of transactions they've done today
    df['recentTransactionsCount'] = [random.randint(0, 10) for _ in range(len(df))]
    
    print(f"Saving our augmented data to {output_csv}...")
    df.to_csv(output_csv, index=False)
    print("All done! You can now use this augmented CSV for training and testing.")

if __name__ == "__main__":
    prepare_synthetic_data()

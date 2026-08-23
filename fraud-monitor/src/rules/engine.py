def run_rules(transaction):
    """
    This function runs simple, hard-coded rules on a transaction.
    If a transaction breaks a rule, we add the rule's name to our list of 'triggered_rules'.
    
    Args:
        transaction: A dictionary containing details about the transaction, like:
                     {'amount': 1500, 'merchantCategory': 'electronics', 'accountId': 'acc_123'}
                     
    Returns:
        triggered_rules: A list of rules this transaction failed.
    """
    triggered_rules = []
    
    # RULE 1: High Transaction Amount
    # Simple check: If the amount is over $1000, flag it. 
    # (In a real system, we'd compare this to the user's historical average!)
    amount = float(transaction.get('Amount', 0))
    if amount > 1000:
        triggered_rules.append("HighAmountDeviation")
        
    # RULE 2: High-Risk Merchant Category
    # If the transaction happened at a merchant type known for fraud, flag it.
    merchant = transaction.get('merchantCategory', '')
    high_risk_merchants = ['crypto_exchange', 'jewelry', 'electronics_wholesale']
    if merchant in high_risk_merchants:
        triggered_rules.append("HighRiskMerchant")
        
    # RULE 3: Velocity Check (Simulated)
    # Velocity means "how fast are transactions happening?".
    # For our simple example, if the transaction data tells us this account 
    # has had more than 5 transactions today, we flag it.
    recent_transactions = int(transaction.get('recentTransactionsCount', 0))
    if recent_transactions > 5:
        triggered_rules.append("HighVelocity")
        
    return triggered_rules

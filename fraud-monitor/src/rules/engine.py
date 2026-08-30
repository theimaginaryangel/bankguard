def run_rules(transaction):
    """
    This function runs simple, heuristic rules on a transaction.
    If a transaction breaks a rule, we add the rule's name to our list of 'triggered_rules'.
    
    Args:
        transaction: A dictionary containing details about the transaction.
                     
    Returns:
        triggered_rules: A list of rules this transaction failed.
    """
    triggered_rules = []
    
    # RULE 1: High Transaction Amount
    raw_amount = transaction.get('Amount')
    if raw_amount is None:
        raw_amount = transaction.get('amount', transaction.get('transaction_dollar_amount', 0))
    try:
        amount = float(raw_amount or 0.0)
    except (ValueError, TypeError):
        amount = 0.0

    if amount > 1000:
        triggered_rules.append("HighAmountDeviation")
        
    # RULE 2: High-Risk Merchant Category
    raw_merchant = transaction.get('merchantCategory')
    if raw_merchant is None:
        raw_merchant = transaction.get('merchant_category', transaction.get('merchant', ''))
    merchant = str(raw_merchant or '').strip().lower()
    high_risk_merchants = ['crypto_exchange', 'jewelry', 'electronics_wholesale', 'wire_transfer', 'casino']
    if merchant in high_risk_merchants:
        triggered_rules.append("HighRiskMerchant")
        
    # RULE 3: Velocity Check (Simulated)
    raw_velocity = transaction.get('recentTransactionsCount')
    if raw_velocity is None:
        raw_velocity = transaction.get('recent_transactions_count', transaction.get('velocity', 0))
    try:
        recent_transactions = int(float(raw_velocity or 0))
    except (ValueError, TypeError):
        recent_transactions = 0

    if recent_transactions > 5:
        triggered_rules.append("HighVelocity")
        
    return triggered_rules

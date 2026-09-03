def analyze_transaction(transaction):

    if transaction.status.lower() == "failed":

        return {
            "revenue_at_risk": True,
            "amount_at_risk": transaction.amount,
            "risk_reason": transaction.failure_reason,
            "recommended_next_step": "recovery_analysis"
        }

    return {
        "revenue_at_risk": False,
        "amount_at_risk": 0,
        "risk_reason": None,
        "recommended_next_step": "no_action_needed"
    }
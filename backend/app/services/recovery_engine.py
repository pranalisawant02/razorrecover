def decide_recovery_action(failure_reason):

    if failure_reason in ["network_error", "payment_timeout"]:
        return {
            "action": "automatic_retry",
            "recoverable": True,
            "recommendation": "Retry payment automatically"
        }

    elif failure_reason == "insufficient_funds":
        return {
            "action": "customer_notification",
            "recoverable": False,
            "recommendation": "Ask customer to use another payment method"
        }

    return {
        "action": "manual_review",
        "recoverable": False,
        "recommendation": "Manual investigation required"
    }
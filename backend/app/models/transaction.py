from pydantic import BaseModel
from datetime import datetime


class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    status: str
    failure_reason: str | None = None
    attempt_count: int = 0
    created_at: datetime
    recovery_status: str = "at_risk"
    recovery_action: str | None = None
    recovered_amount: float = 0.0
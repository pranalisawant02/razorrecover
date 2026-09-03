from pydantic import BaseModel


class TransactionCreate(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    status: str
    failure_reason: str | None = None
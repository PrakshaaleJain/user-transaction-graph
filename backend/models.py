from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    payment_method: Optional[str] = None

class Transaction(BaseModel):
    txn_id: str
    sender_id: str
    receiver_id: str
    amount: float
    device_id: Optional[str] = None
    ip_address: Optional[str] = None

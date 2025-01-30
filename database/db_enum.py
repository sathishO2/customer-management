from enum import Enum

class StatusEnum(Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"

class PaymentMethodEnum(Enum):
    credit_card = "Credit Card"
    debit_card = "Debit Card"
    paypal = "PayPal"

class OrderStatusEnum(Enum):
    pending = "Pending"
    processing = "Processing"
    delivered = "Delivered"
    cancelled = "Cancelled"
    returned = "Returned"

    
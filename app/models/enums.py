from enum import Enum


class OperationType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"


class PaymentType(str, Enum):
    CASH = "cash"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    REFUND_TO_DEBIT = "refund_to_debit"
    REFUND_TO_CREDIT = "refund_to_credit"


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"
    GBP = "GBP"


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


EXPENSE_PAYMENT_TYPES = [
    PaymentType.CASH,
    PaymentType.DEBIT_CARD,
    PaymentType.CREDIT_CARD,
]

INCOME_PAYMENT_TYPES = [
    PaymentType.CASH,
    PaymentType.DEBIT_CARD,
    PaymentType.REFUND_TO_DEBIT,
    PaymentType.REFUND_TO_CREDIT,
]

PAYMENT_TYPE_LABELS = {
    PaymentType.CASH: "Cash",
    PaymentType.DEBIT_CARD: "Debit Card",
    PaymentType.CREDIT_CARD: "Credit Card",
    PaymentType.REFUND_TO_DEBIT: "Refund to Debit",
    PaymentType.REFUND_TO_CREDIT: "Refund to Credit",
}

OPERATION_TYPE_LABELS = {
    OperationType.EXPENSE: "Expense",
    OperationType.INCOME: "Income",
}

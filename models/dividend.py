from enum import Enum
from datetime import datetime

from models.security_identifier import SecurityIdentifier


class DividendType(Enum):
    NONQUALIFIED = 0
    QUALIFIED = 1
    SECTION_199A = 2
    TAX_EXEMPT = 3


class Dividend:
    def __init__(self):
        self.date: datetime = datetime.now()
        self.security_id = SecurityIdentifier()
        self.amount: float = 0
        self.type: DividendType = DividendType.NONQUALIFIED

    def __str__(self):
        return f"Dividend: {self.security_id} DATE {self.date} AMOUNT {self.amount}"
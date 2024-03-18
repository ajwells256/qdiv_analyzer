from enum import Enum
from typing import Optional, Union


class By(Enum):
    CUSIP = 1
    SYMBOL = 2


class SecurityIdentifier:
    def __init__(self, cusip: Optional[str] = None, symbol: Optional[str] = None):
        if cusip is None and symbol is None:
            raise Exception("A security must be identified by either a CUSIP or a Symbol")

        self.cusip: Union[str, None] = cusip
        self.symbol: Union[str, None] = symbol

    def __str__(self):
        return f"SYMB: {self.symbol} CUSIP {self.cusip}"

from enum import Enum
from datetime import datetime
from typing import Dict, cast
from logging import getLogger
from locale import atof

from models.security_identifier import SecurityIdentifier
from utilities.user_selection import user_selector

logger = getLogger(__name__)


class DividendType(Enum):
    NONQUALIFIED = 0
    QUALIFIED = 1
    SECTION_199A = 2
    TAX_EXEMPT = 3


class Dividend:
    def __init__(self,
        data: Dict[str, object],
        value_key: str
    ):
        self.date: datetime = datetime.now()
        self.security_id = SecurityIdentifier()

        self.value: float = 0
        if data[value_key] is float:
            self.value = cast(float, data[value_key])
        elif data[value_key] is str:
            self.value = atof(cast(str, data[value_key]))
        else:
            raise Exception("The value of the dividend must be a string or a float")
        data[value_key] = self.value  # coerce to float

        self.type: DividendType = DividendType.NONQUALIFIED
        self.data = data

        self._value_key = value_key

    @property
    def symbol(self) -> str:
        assert self.security_id.symbol is not None, (
            "tried to get an unset symbol, the security should be hydrated")
        return self.security_id.symbol

    def disqualify(self, disqualification_amount) -> "Dividend":
        data_copy = self.data.copy()
        self.value -= disqualification_amount
        self.data[self._value_key] -= disqualification_amount
        data_copy[self._value_key] = disqualification_amount

        new_div = Dividend(data_copy, self._value_key)
        new_div.security_id = self.security_id
        return new_div

    def add_note(self, note: str):
        if "notes" in self.data and self.data["notes"] is str:
            existing_note = self.data["notes"]
            self.data["notes"] = f"{existing_note}; {note}"
        else:
            if "notes" in self.data:
                logger.warn("Origianl notes field of non-string type will be renamed to 'original_notes' as a note is being added")
                self.data["original_notes"] = self.data["notes"]
            self.data["notes"] = note

    def __str__(self):
        return f"Dividend: {self.security_id} DATE {self.date} AMOUNT {self.value}"

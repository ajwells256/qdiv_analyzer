from enum import Enum
from datetime import datetime
from dateutil import parser
from typing import Dict, cast
from logging import getLogger
from locale import atof

from models.security_identifier import SecurityIdentifier
from utilities.user_selection import user_selector

logger = getLogger(__name__)


class DividendType(Enum):
    NonQualified = 0
    Qualified = 1
    Section_199A = 2
    Tax_Exempt = 3
    Tax_Withheld = 4

    @classmethod
    def from_str(cls, type: str) -> "DividendType":
        classification = user_selector.user_selection(
            f"Which of the following best categorizes this dividend: {type}?", DividendType._member_names_)
        return DividendType(classification)

    def __str__(self) -> str:
        return ["Non-Qualified", "Qualified", "Section 199A", "Tax Exempt", "Tax Withheld"][self.value]


class FieldNames(Enum):
    RecordDate = "Record Date"
    CUSIP = "CUSIP"
    Value = "Amount"
    Type = "Type"


class Dividend:
    def __init__(self,
        data: Dict[str, object],
        date_key: str,
        cusip_key: str,
        value_key: str,
        type_key: str
    ):
        self.date: datetime = parser.parse(str(data[date_key]))
        self.security_id = SecurityIdentifier(cusip=str(data[cusip_key]))

        self.value: float = 0
        if type(data[value_key]) is float:
            self.value = cast(float, data[value_key])
        elif type(data[value_key]) is str:
            self.value = atof(cast(str, data[value_key]))
        else:
            raise Exception("The value of the dividend must be a string or a float")
        data[value_key] = self.value  # coerce to float

        if type(data[type_key]) is DividendType:
            self.type: DividendType = cast(DividendType, data[type_key])
            data[type_key] = str(data[type_key])  # coerce back to string
        else:
            self.type = DividendType.from_str(str(data[type_key]))

        # persist data, as it will be the source of truth
        self.data = data

        self._value_key = value_key
        self._date_key = date_key
        self._cusip_key = cusip_key
        self._type_key = type_key

    @property
    def symbol(self) -> str:
        assert self.security_id.symbol is not None, (
            "tried to get an unset symbol, the security should be hydrated")
        return self.security_id.symbol

    def standardized_csv_data(self) -> Dict[str, object]:
        '''Standardizes and returns the data representation of this dividend.
        This is particularly imporant if dividends coming from multiple data sources contain nonstandard field names
        '''
        # replace dictionary keys with their standard values
        self.data[FieldNames.RecordDate.value] = self.data.pop(self._date_key)
        self.data[FieldNames.CUSIP.value] = self.data.pop(self._cusip_key)
        self.data[FieldNames.Value.value] = self.data.pop(self._value_key)
        self.data[FieldNames.Type.value] = self.data.pop(self._type_key)

        # update key values to stay internally consistent
        self._date_key = FieldNames.RecordDate.value
        self._cusip_key = FieldNames.CUSIP.value
        self._value_key = FieldNames.Value.value
        self._type_key = FieldNames.Type.value
        return self.data

    def disqualify(self, disqualification_amount) -> "Dividend":
        data_copy = self.data.copy()
        disqualification_amount = float(disqualification_amount)
        self.value -= disqualification_amount
        self.data[self._value_key] -= disqualification_amount
        data_copy[self._value_key] = disqualification_amount
        data_copy[self._type_key] = DividendType.NonQualified

        new_div = Dividend(data_copy, self._date_key, self._cusip_key, self._value_key, self._type_key)
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

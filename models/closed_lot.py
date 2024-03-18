from typing import Dict
from datetime import datetime

from logging import getLogger

from models.security_identifier import SecurityIdentifier

logger = getLogger(__name__)


class ClosedLot:
    def __init__(
        self,
        open_date_name: str,
        close_date_name: str,
        data: Dict[str, object],
        strptime_fmt: str = "%Y-%m-%d",
    ):
        required_keywords = [
            "symbol",
            "cusip",
            "quantity",
            open_date_name.lower(),
            close_date_name.lower(),
        ]
        for keyword in required_keywords:
            assert keyword in map(
                str.lower, data
            ), f"Required field {keyword} missing from {data.keys()}"

        def lookup(key: str):
            matching_keys = [k for k in data.keys() if k.lower() == key.lower()]
            orig_key = matching_keys[0]
            return data[orig_key]

        def parse_date(key: str) -> datetime:
            try:
                date = lookup(key)
                return datetime.strptime(date, strptime_fmt)
            except ValueError:
                logger.error(f"Failed to parse date {date} using {strptime_fmt}")
                raise

        self.data = data

        self.security_id = SecurityIdentifier(symbol=lookup("symbol"), cusip=lookup("cusip"))
        self.quantity: float = float(lookup("quantity"))
        self.open_date = parse_date(open_date_name)
        self.close_date = parse_date(close_date_name)

        self._holding_period = self.close_date - self.open_date
        self._strptime_fmt = strptime_fmt

    @property
    def holding_period(self) -> int:
        """Gets the holding period in days of the lot"""
        return self._holding_period.days

    def __str__(self):
        timefmt = "%Y-%m-%d"
        return (
            f"Closed Lot: {self.security_id} "
            f"Open {self.open_date.strftime(timefmt)} Close {self.close_date.strftime(timefmt)}"
        )

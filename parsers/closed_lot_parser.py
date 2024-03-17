from typing import Dict, List
import csv
from datetime import datetime

from logging import getLogger

from utilities.UserSelection import user_selector

logger = getLogger(__name__)

"""
Trading data from Wealthfront can be obtained from:
    Logging into Wealthfront.com (not the app)
    Then click on the taxable account you want to get information for
    Click on Manage on the top right of the page in purple
    Click on View cost basis details near the bottom of the page
    Select either Realized gain/loss and select Download CSV on the top right of the page

TODO: Robinhood features.
Robinhood provided a 'consolidated_transactions.csv' this year which, after some
simple massaging and expanded tooling, should work with this tool as well.
    For example, Long term sales are missing an open date since it isn't important.
"""


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

        self.symbol: str = lookup("symbol")
        self.cusip: str = lookup("cusip")
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
        return f"SYMB {self.symbol} CUSIP {self.cusip} Open {self.open_date.strftime(timefmt)} Close {self.close_date.strftime(timefmt)}"


def read_closed_lots(filename: str) -> List[ClosedLot]:
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None, f"Failed to read field names from {filename}"
        fieldnames = list(reader.fieldnames)
        open_date_idx = user_selector.user_selection("Which of these should be the open date for the lot?", fieldnames)
        close_date_idx = user_selector.user_selection("Which of these should be the close date for the lot?", fieldnames)

        transactions = [
            ClosedLot(fieldnames[open_date_idx], fieldnames[close_date_idx], row)
            for row in reader
        ]
    return transactions


transactions = read_closed_lots("Taxable_Closed_Lots.csv")
for t in transactions:
    if t.holding_period < 61:
        print(t)

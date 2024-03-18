from typing import List
import csv

from logging import getLogger

from models.closed_lot import ClosedLot
from utilities.user_selection import user_selector


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

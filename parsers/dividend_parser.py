import csv
from typing import List, Set
from datetime import datetime
from logging import getLogger

from models.dividend import Dividend, FieldNames
from utilities.user_selection import user_selector

logger = getLogger(__name__)

"""
Dividend data can be obtained from the 1099 PDF. The tool
1099_Parser (https://github.com/ajwells256/1099-Parser) is one
way to turn the PDF data into a csv for use with this analyzer.
"""


def read_dividends(filename: str) -> List[Dividend]:
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None, f"Failed to read field names from {filename}"
        fieldnames = list(reader.fieldnames)
        date_idx = user_selector.user_selection("Which of these is the date?", fieldnames)
        cusip_idx = user_selector.user_selection("Which of these is the cusip?", fieldnames)
        value_idx = user_selector.user_selection("Which of these is the dollar value?", fieldnames)
        types_idx = user_selector.user_selection("Which of these is the dividend type?", fieldnames)

        transactions = [
            Dividend(row, fieldnames[date_idx], fieldnames[cusip_idx], fieldnames[value_idx], fieldnames[types_idx])
            for row in reader
        ]
    return transactions


def write_dividends(dividends: List[Dividend]):
    filename = f"adjusted_dividends_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"

    list(map(Dividend.standardized_csv_data, dividends))

    if len(dividends) > 0:
        keys: Set[str] = set()
        for div in dividends:
            keys.update(div.data.keys())

        # ensure the csv columns are sensibly orderede
        fieldnames = [FieldNames.RecordDate.value, FieldNames.CUSIP.value, FieldNames.Value.value, FieldNames.Type.value]
        fieldnames += [nonstandard_key for nonstandard_key in keys if nonstandard_key not in fieldnames]
        with open(filename, "w") as f:
            writer = csv.DictWriter(f, fieldnames)
            writer.writeheader()
            writer.writerows([d.data for d in dividends])
        logger.info(f"Wrote adjusted dividends to {filename}")

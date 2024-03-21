import csv
from typing import List, Set
from datetime import datetime
from logging import getLogger

from models.dividend import Dividend, FieldName
from utilities.user_selection import user_selector

logger = getLogger(__name__)

"""
Dividend data can be obtained from the 1099 PDF. The tool
1099_Parser (https://github.com/ajwells256/1099-Parser) is one
way to turn the PDF data into a csv for use with this analyzer.
"""


def get_fieldname_index(fieldnames: List[str], fieldname: FieldName, user_friendly_desc: str) -> int:
    '''Tries to parse the column index of a standard fieldname out of the provided field names.
    Asks the user for input if it can't be determined'''
    if fieldname.value in fieldnames:
        return fieldnames.index(fieldname.value)
    else:
        return user_selector.user_selection(f"Which of these is the {user_friendly_desc}?", fieldnames)


def read_dividends(filename: str) -> List[Dividend]:
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None, f"Failed to read field names from {filename}"
        fieldnames = list(reader.fieldnames)

        date_idx = get_fieldname_index(fieldnames, FieldName.RecordDate, "date")
        cusip_idx = get_fieldname_index(fieldnames, FieldName.CUSIP, "cusip")
        value_idx = get_fieldname_index(fieldnames, FieldName.Amount, "dollar value")
        type_idx = get_fieldname_index(fieldnames, FieldName.Type, "dividend type")

        transactions = [
            Dividend(row, fieldnames[date_idx], fieldnames[cusip_idx], fieldnames[value_idx], fieldnames[type_idx])
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
        fieldnames = [FieldName.RecordDate.value, FieldName.CUSIP.value, FieldName.Amount.value, FieldName.Type.value]
        fieldnames += [nonstandard_key for nonstandard_key in keys if nonstandard_key not in fieldnames]
        with open(filename, "w") as f:
            writer = csv.DictWriter(f, fieldnames)
            writer.writeheader()
            writer.writerows([d.data for d in dividends])
        logger.info(f"Wrote adjusted dividends to {filename}")

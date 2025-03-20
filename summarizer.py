from functools import reduce
from itertools import chain
import numpy as np
from typing import List

from logging import getLogger
from argparse import Namespace

# from models.closed_lot import ClosedLot
from models.dividend import Dividend, DividendType
# from parsers.closed_lot_parser import read_closed_lots
from parsers.dividend_parser import read_dividends

logger = getLogger(__name__)


def dividend_summary(dividends: List[Dividend]) -> np.ndarray:
    qualified_dividends = sum(d.value for d in dividends if d.type == DividendType.Qualified)
    section_199a_dividends = sum(d.value for d in dividends if d.type == DividendType.Section_199A)
    tax_paid = sum(d.value for d in dividends if d.type == DividendType.Tax_Withheld)
    exempt_dividends = sum(d.value for d in dividends if d.type == DividendType.Tax_Exempt)
    total_ordinary_dividends = sum(d.value for d in dividends if d.type == DividendType.NonQualified) + \
        qualified_dividends + section_199a_dividends

    summary = np.array([total_ordinary_dividends, qualified_dividends, section_199a_dividends, tax_paid, exempt_dividends])

    print_dividend_summary(summary)
    return summary


def print_dividend_summary(dividend_summary: np.ndarray):

    print(f""">>> Dividends and Distributions
>>> 1a Total ordinary dividends:      {float(dividend_summary[0]):0.2f}
>>> 1b Qualified dividends:           {float(dividend_summary[1]):0.2f}
>>> 5  Section 199A dividends:        {float(dividend_summary[2]):0.2f}
>>> 7  Foreign tax paid:              {float(dividend_summary[3]):0.2f}
>>> 12 Exempt-interest dividends:     {float(dividend_summary[4]):0.2f}
""")


def summarize(args: Namespace):
    logger.info("Running summerizer")

    # read all input CSVs
    # flattened_lots_files = chain.from_iterable(args.lots)
    flattened_dividends_files = chain.from_iterable(args.dividends)

    # handle each file separately for granularity of data
    dividends_summaries = []
    for dividend_file in flattened_dividends_files:
        dividends = read_dividends(dividend_file)

        dividends_summaries.append(dividend_summary(dividends))

    if len(list(flattened_dividends_files)) > 1:
        full_dividends = reduce(lambda acc, next: acc + next, dividends_summaries, np.zeros_like(dividends_summaries[0]))
        print(">>> Aggregated Total")
        print_dividend_summary(full_dividends)

    # TODO: lots
    # closed_lots_summaries = []
    # for closed_lot_file in flattened_lots_files:
    #     closed_lots_summaries.append(lot_summary(read_closed_lots(closed_lot_file)))

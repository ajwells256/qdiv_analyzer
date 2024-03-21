from datetime import datetime
from functools import reduce
from itertools import chain
import numpy as np
from typing import Tuple, Dict, List, cast

from logging import getLogger
from argparse import Namespace

# from models.closed_lot import ClosedLot
from models.dividend import Dividend, DividendType
from models.security_identifier import SecurityIdentifier
# from parsers.closed_lot_parser import read_closed_lots
from parsers.dividend_parser import read_dividends

logger = getLogger(__name__)


def dividend_summary(dividends: List[Dividend]) -> np.ndarray:
    qualified_dividends = sum(d.value for d in dividends if d.type == DividendType.Qualified)
    section_199a_dividends = sum(d.value for d in dividends if d.type == DividendType.Section_199A)
    tax_paid = sum(d.value for d in dividends if d.type == DividendType.Tax_Withheld)
    exempt_dividends = sum(d.value for d in dividends if d.type == DividendType.Tax_Exempt)
    total_dividends = sum(d.value for d in dividends)

    summary = np.array([total_dividends, qualified_dividends, section_199a_dividends, tax_paid, exempt_dividends])

    print_dividend_summary(summary)
    return summary


def dividends_verbose(dividends: List[Dividend]):
    def aggregate_list(acc: Dict[Tuple[str, datetime, DividendType], float], dividend: Dividend) -> Dict[Tuple[str, datetime, DividendType], float]:
        assert dividend.security_id.cusip is not None, f"encountered a dividend without a cusip: {dividend}"
        key = (dividend.security_id.cusip, dividend.date, dividend.type)
        if key in acc:
            acc[key] += dividend.value
        else:
            acc[key] = dividend.value
        return acc

    dividends_breakdown = reduce(aggregate_list, dividends, cast(Dict[Tuple[str, datetime, DividendType], float], {}))

    # sort on the date, the second value of the key tuple
    sorted_dividends_breakdown = sorted(dividends_breakdown.keys(), key=lambda k: (k[0], k[1]))

    run_sum: float = 0
    last_cusip = ""
    for cusip, date, type in sorted_dividends_breakdown:
        if last_cusip != cusip:
            if run_sum > 0:
                print(f"Total: {run_sum:0.2f}".rjust(62), end="\n\n")
                run_sum = 0

            print(f"{cusip}".ljust(20), end="")
            last_cusip = cusip
        else:
            print("".ljust(20), end="")
        print(f"{date.date()}".ljust(15), end="")
        print(f"{type.value}".ljust(20), end="")

        value = dividends_breakdown[(cusip, date, type)]
        print(f"{value:0.2f}".rjust(7))
        run_sum += value


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
        if args.verbose:
            dividends_verbose(dividends)

        dividends_summaries.append(dividend_summary(dividends))
    full_dividends = reduce(lambda acc, next: acc + next, dividends_summaries, np.zeros_like(dividends_summaries[0]))
    print(">>> Aggregated Total")
    print_dividend_summary(full_dividends)

    # TODO: lots
    # closed_lots_summaries = []
    # for closed_lot_file in flattened_lots_files:
    #     closed_lots_summaries.append(lot_summary(read_closed_lots(closed_lot_file)))

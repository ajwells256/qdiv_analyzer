from datetime import datetime
from functools import reduce
from itertools import chain
from pandas.core.series import Series
from typing import List, Union, Tuple, Iterable

from logging import getLogger
from argparse import Namespace

from models.closed_lot import ClosedLot
from models.dividend import Dividend, DividendType
from models.security_identifier import SecurityIdentifier
from parsers.closed_lot_parser import read_closed_lots
from parsers.dividend_parser import read_dividends, write_dividends
from repositories.yahoo_repository import YahooRepository

logger = getLogger(__name__)


def get_dividend_exdate(dividend: Dividend, dividend_exdates: Series) -> Union[datetime, None]:
    '''Get the latest exdate still preceding the dividend payment date from the provided list of exdates'''
    parsed_exdates = map(lambda x: datetime(x.year, x.month, x.day), dividend_exdates.keys())
    applicable_exdates = [exdate for exdate in parsed_exdates if exdate < dividend.date]

    if len(applicable_exdates) == 0:
        printable_exdates = ','.join(map(lambda d: d.strftime('%Y-%m-%d'), parsed_exdates))
        logger.error(f"For dividend {dividend} got no valid exdates (out of: {printable_exdates})")
        return None

    return max(applicable_exdates)


def identify_and_separate_disqualified_dividends(
        dividends: List[Dividend],
        lots_with_short_holding_periods: List[ClosedLot],
        securities_with_qual_divs: Iterable[SecurityIdentifier],
        dividend_exdates: Series) -> Tuple[List[Dividend], bool]:
    '''Finds dividends which should be disqualified. For any dividends that should be disqualified,
    part or all of the dividend will be split into a new dividend with the proper type. The original
    dividend will be updated to have the proper value

    A new list of dividends will be returned, with the updated original dividends as well as the newly
    created ones.
    '''
    processed_dividends = [d for d in dividends if d.type != DividendType.Qualified]
    adjustment_occurred = False

    # ensure that each security gets dealt with once
    securities_with_qual_divs = set(securities_with_qual_divs)
    for sec in securities_with_qual_divs:
        qualified_relevant_dividends = [d for d in dividends if d.security_id == sec and d.type == DividendType.Qualified]
        for div in qualified_relevant_dividends:
            cusip_exdate_infos: Series = dividend_exdates[div.symbol]
            exdate = get_dividend_exdate(div, cusip_exdate_infos)
            if exdate:
                '''Caveat: Assume that securities analyzed are common stock
                > If the payment is from a common stock you are required to have held it for more than 60 days
                > during the 121-day period that begins 60 days before the ex-dividend date of the dividend
                To get a dividend, you must hold the stock on the exdate. Therefore, the question of whether a stock
                was held for 61 of the 121 days can be rephrased as whether the exdate fell within any holding periods
                shorter than 61 days. Any holding periods longer than 60 days containing the exdate are naturally ok,
                and any short holding periods not containing the exdate wouldn't have resulted in any dividends in the
                first place.
                '''
                disqualified_lots = [
                    lot for lot in lots_with_short_holding_periods
                    if lot.security_id == sec and lot.open_date <= exdate and exdate <= lot.close_date
                ]

                if len(disqualified_lots) > 0:
                    # sometimes a fraction of the dividend is qualified. Calculate the total for the security
                    # on the dividend date to then quanitfy what fraction of the dividend was qualified
                    related_dividends = [d for d in dividends if d.security_id == sec and d.date == div.date]

                    # purposefully avoid the foreign tax withheld values
                    total_dividend_amount = sum(d.value for d in related_dividends if d.value > 0)
                    qualified_percentage = div.value / total_dividend_amount

                    dividend_value_per_share = cusip_exdate_infos[exdate.date()]

                    # create a new dividend from the disqualified value of the old one
                    disqualified_shares = sum(lot.quantity for lot in disqualified_lots)
                    disqualified_value = round(disqualified_shares * dividend_value_per_share * qualified_percentage, 2)
                    new_div = div.disqualify(disqualified_value)
                    div.add_note((f"Disqualified ${disqualified_value}. The dividend on {exdate.date()} had value"
                                  f" ${dividend_value_per_share} per share. {qualified_percentage * 100:0.2f}% of the dividend"
                                  f" value was classified as qualified. {disqualified_shares} shares were not held for 61"
                                  f" days of the relevant 121 day period, which are: {';'.join(map(str, disqualified_lots))}"
                    ))
                    new_div.add_note(f"Synthesized nonqualified dividend due to: {';'.join(map(str, disqualified_lots))}")

                    processed_dividends.append(div)
                    processed_dividends.append(new_div)
                    adjustment_occurred = True
                else:
                    processed_dividends.append(div)
    return (processed_dividends, adjustment_occurred)


def analyze_qualified_dividends(args: Namespace):
    logger.info("Running qualified dividends analysis")
    yahoo_repository = YahooRepository()

    # read all input CSVs
    flattened_lots_files = chain.from_iterable(args.lots)
    flattened_dividends_files = chain.from_iterable(args.dividends)
    closed_lots: List[ClosedLot] = reduce(lambda acc, next: acc + read_closed_lots(next), flattened_lots_files, [])
    dividends: List[Dividend] = reduce(lambda acc, next: acc + read_dividends(next), flattened_dividends_files, [])

    # hydrate all the security identifiers
    list(map(lambda x: x.hydrate(yahoo_repository), [lots.security_id for lots in closed_lots]))
    list(map(lambda x: x.hydrate(yahoo_repository), [divs.security_id for divs in dividends]))

    # get all securities that had qualified dividends
    securities_with_qual_divs = set([d.security_id for d in dividends if d.type == DividendType.Qualified])

    # get closed lots for those securities which had short holding periods
    lots_with_short_holding_periods = [lot for lot in closed_lots
                                       if lot.security_id in securities_with_qual_divs and lot.holding_period < 61]

    if len(lots_with_short_holding_periods) > 0:
        # fetch dividend information those securities with holding periods less than 60 days
        dividend_exdates = yahoo_repository.get_dividend_exdates(
            [lot.security_id for lot in lots_with_short_holding_periods if lot.holding_period < 61],
            args.year
        )

        if dividend_exdates is None:
            raise Exception("Encountered an error fetching dividend exdate information")

        # produce an updated csv if there are dividends which have been disqualified
        new_dividends, adjustment_occurred = identify_and_separate_disqualified_dividends(
            dividends,
            lots_with_short_holding_periods,
            securities_with_qual_divs,
            dividend_exdates
        )

        if adjustment_occurred:
            write_dividends(new_dividends)

    logger.info("Analysis complete")

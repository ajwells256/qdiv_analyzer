from typing import Dict, List, Tuple, Union
from yahooquery import Ticker, search  # type: ignore
from pandas.core.series import Series
from datetime import datetime

from models.security_identifier import By
from repositories.dividend_exdate_repository import DividendExdateRepository

from logging import getLogger

logger = getLogger(__name__)


class YahooDividendExdateRepository(DividendExdateRepository):
    def __init__(self):
        self.cusip_cache = {}

    def get_dividend_exdates(self, by: By, lookup: Union[str, List[str]], tax_year: int) -> Tuple[Union[Series, None], Dict[str, str]]:
        """ Gets the dividend history using the specified lookup string for the specified tax year

        Keyword Arguments:
        by -- Hint whether the lookup string is a CUSIP or a symbol
        lookup -- the CUSIP or symbol of the security (or a list, for multiple)
        tax_year -- the integer of the year for which to query

        Returns:
        Returns the dividend history, as reported by yahoo finance.
        Caveat, this seems to generally return just a single date (as well as what appears to be the amount per share)
        The date has, in the examples I've checked, been the ex dividend date. For the purposes of analysis, consumers of this
        method should use some method to validate it's the correct date. I'm thinking comparing with the date on which dividends
        were received should give a sense of whether its tracking record date or exdate.
        """

        # normalize lookup to a list
        if isinstance(lookup, str):
            lookup = [lookup]

        tickers = []

        if by == By.CUSIP:
            for cusip in lookup:
                ticker = None
                if (cusip in self.cusip_cache.keys()):
                    ticker = self.cusip_cache[cusip]
                else:
                    ticker = self._get_ticker_from_cusip(cusip)
                    self.cusip_cache[cusip] = ticker

                # skip the ticker if it couldn't be resolved to a symbol
                if (ticker is not None):
                    tickers.append(ticker)

        elif by == By.SYMBOL:
            tickers = lookup

        # have list of ticker symbols, fetch their dividend history
        dividend_history = None
        if (len(tickers) > 0):
            yahoo_tickers = Ticker(tickers)
            dividend_history_frame = yahoo_tickers.dividend_history(
                datetime(tax_year, 1, 1), datetime(tax_year + 1, 1, 1))
            dividend_history = dividend_history_frame['dividends']

        return dividend_history, self.cusip_cache

    def _get_ticker_from_cusip(self, cusip: str) -> Union[str, None]:
        ticker = None
        search_results = search(cusip, quotes_count=1)
        quotes = search_results['quotes']
        if len(quotes) < 1:
            usr_input = input(
                f"Error: failed to lookup ticker for CUSIP: {cusip}. Enter it manually or hit enter to skip:\n")
            if (len(usr_input) != 0):
                ticker = usr_input.rstrip("\n")
        else:
            # got a quote
            ticker = quotes[0]['symbol']
            if len(quotes) > 1:
                logger.warn(f"Got multiple hits for CUSIP {cusip}: {','.join([q['symbol'] for q in quotes])}. Will use {ticker}")
        return ticker

from typing import List, Union, cast
from yahooquery import Ticker, search  # type: ignore
from pandas.core.series import Series
from datetime import datetime
from logging import getLogger

from models.security_identifier import SecurityIdentifier
from repositories.dividend_exdate_repository import DividendExdateRepository
from repositories.symbol_repository import SymbolRepository
from utilities.user_selection import user_selector


logger = getLogger(__name__)


class YahooRepository(DividendExdateRepository, SymbolRepository):
    def __init__(self):
        pass

    def get_dividend_exdates(self, query: Union[SecurityIdentifier, List[SecurityIdentifier]], tax_year: int) -> Union[Series, None]:
        """ Gets the dividend history for the specified tax year

        Keyword Arguments:
        security_ids -- the security identifier (or a list, for multiple)
        tax_year -- the integer of the year for which to query

        Returns:
        Returns the dividend history, as reported by yahoo finance.
        Caveat, this seems to generally return just a single date (as well as what appears to be the amount per share)
        The date has, in the examples I've checked, been the ex dividend date. For the purposes of analysis, consumers of this
        method should use some method to validate it's the correct date. I'm thinking comparing with the date on which dividends
        were received should give a sense of whether its tracking record date or exdate.
        """

        # normalize lookup to a list
        if isinstance(query, str):
            query = [query]

        query = cast(List[SecurityIdentifier], query)

        # ensure that all the symbols are available
        map(lambda x: x.hydrate(self), query)

        securities_missing_symbols = [s for s in query if s.symbol is None]
        if any(securities_missing_symbols):
            logger.error(("All the tickers should have be populated but got "
                          f"{','.join([s.cusip for s in securities_missing_symbols])} CUSIPS without symbols"))  # type: ignore
            return None

        tickers: List[str] = [cast(str, security_id.symbol) for security_id in query]

        logger.debug(f"Fetching dividend information for {','.join(tickers)} from Yahoo Query")

        # have list of ticker symbols, fetch their dividend history
        yahoo_tickers = Ticker(tickers)
        dividend_history_frame = yahoo_tickers.dividend_history(
            datetime(tax_year, 1, 1), datetime(tax_year + 1, 1, 1))
        dividend_history = dividend_history_frame['dividends']

        return dividend_history

    def get_ticker_from_cusip(self, cusip: str) -> str:
        logger.debug(f"Looking up {cusip} with Yahoo Query")
        search_results = search(cusip, quotes_count=1)
        quotes = search_results['quotes']
        if len(quotes) < 1:
            usr_input = input(f"Error: failed to lookup ticker for CUSIP: {cusip}. Enter it manually: ")
            ticker = usr_input.rstrip("\n")
        elif len(quotes) == 1:
            ticker = quotes[0]['symbol']
        else:
            all_tickers = [q['symbol'] for q in quotes]
            logger.warn(f"Got multiple hits for CUSIP {cusip}: {','.join(all_tickers)}.")
            ticker_idx = user_selector.user_selection(f"Got multiple hits for CUSIP {cusip}. Which is the right symbol?", all_tickers)
            ticker = all_tickers[ticker_idx]
        return ticker

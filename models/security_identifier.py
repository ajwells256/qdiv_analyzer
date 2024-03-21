from enum import Enum
from typing import Dict, Optional, Union, cast
from logging import getLogger

from repositories.symbol_repository import SymbolRepository

logger = getLogger(__name__)

cusip_to_symbol_cache: Dict[str, str] = {}


class By(Enum):
    CUSIP = 1
    SYMBOL = 2


class SecurityIdentifier:
    def __init__(self, cusip: Optional[str] = None, symbol: Optional[str] = None):
        if cusip is None and symbol is None:
            raise Exception("A security must be identified by either a CUSIP or a Symbol")

        self.cusip: Union[str, None] = cusip
        self.symbol: Union[str, None] = symbol

    def hydrate(self, symbol_repository: SymbolRepository):
        '''Prepares the identifier for comparison by querying the symbol repository for missing data
        Currently, there is no method for querying Symbol -> CUSIP because that hasn't been required so far.
        '''
        if self.cusip and not self.symbol:
            if self.cusip not in cusip_to_symbol_cache:
                cusip_to_symbol_cache[self.cusip] = symbol_repository.get_ticker_from_cusip(self.cusip)
            self.symbol = cusip_to_symbol_cache[self.cusip]
        elif self.symbol and not self.cusip:
            raise NotImplementedError("Need a new method for getting CUSIP from Symbol")

    def __eq__(self, value) -> bool:
        if isinstance(value, SecurityIdentifier):
            value = cast(SecurityIdentifier, value)
            if (value.cusip and not self.cusip) and (value.symbol and not self.symbol):
                logger.error("Error comparing securities which don't have the same fields defined: %s %s",
                    str(value), str(self))
                raise Exception("Ensure that all security identifiers are hydrated before comparing them")
            return (value.cusip is not None and self.cusip is not None and value.cusip == self.cusip) or \
                (value.symbol is not None and self.symbol is not None and value.symbol == self.symbol)
        else:
            return NotImplemented

    def __hash__(self) -> int:
        if self.symbol:
            return hash(self.symbol)
        else:
            raise Exception("Ensure that all security identifiers are hydrated before comparing them")

    def __str__(self):
        if self.symbol is None:
            raise Exception("Ensure that all security identifiers are hydrated")
        result = self.symbol
        if self.cusip is not None:
            result += f" ({self.cusip})"
        return result

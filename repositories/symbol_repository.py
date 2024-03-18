
from abc import ABC, abstractmethod


class SymbolRepository(ABC):
    @abstractmethod
    def get_ticker_from_cusip(self, cusip: str) -> str:
        raise NotImplementedError()

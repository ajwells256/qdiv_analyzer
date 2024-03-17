
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Tuple, Union
from pandas.core.series import Series

class By(Enum):
    CUSIP = 1
    SYMBOL = 2

class DividendExdateRepository(ABC):
    @abstractmethod
    def get_dividend_exdates(self, by: By, lookup: Union[str, List[str]], tax_year: int) -> Tuple[Union[Series, None], Dict[str, str]]:
        raise NotImplementedError()
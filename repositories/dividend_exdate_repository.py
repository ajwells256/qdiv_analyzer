
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Union
from pandas.core.series import Series

from models.security_identifier import By


class DividendExdateRepository(ABC):
    @abstractmethod
    def get_dividend_exdates(self, by: By, lookup: Union[str, List[str]], tax_year: int) -> Tuple[Union[Series, None], Dict[str, str]]:
        raise NotImplementedError()
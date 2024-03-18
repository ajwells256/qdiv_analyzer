
from abc import ABC, abstractmethod
from typing import List, Union
from pandas.core.series import Series

from models.security_identifier import SecurityIdentifier


class DividendExdateRepository(ABC):
    @abstractmethod
    def get_dividend_exdates(self, lookup: Union[SecurityIdentifier, List[SecurityIdentifier]], tax_year: int) -> Union[Series, None]:
        raise NotImplementedError()

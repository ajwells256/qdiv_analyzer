import csv
from typing import List
from datetime import datetime
from logging import getLogger

from models.dividend import Dividend

logger = getLogger(__name__)


def read_dividends(filename: str) -> List[Dividend]:
    raise NotImplementedError


def write_dividends(dividends: List[Dividend]):
    filename = f"adjusted_dividends_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"

    if len(dividends) > 0:
        keys = set(dividends[0].data.keys())
        keys.add("notes")  # if we're writing dividends, at least some of them will have notes
        with open(filename, "w") as f:
            writer = csv.DictWriter(f, keys)
            writer.writeheader()
            writer.writerows([d.data for d in dividends])
        logger.info(f"Wrote adjusted dividends to {filename}")

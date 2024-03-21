from typing import List, Optional, Dict, Union

from datetime import datetime

import csv

from logging import getLogger

logger = getLogger(__name__)


def try_parse_int(input: str) -> bool:
    try:
        int(input)
        return True
    except Exception:
        return False


class UserSelection:
    def __init__(self):
        self.selections: List[Dict[str, str]] = []
        self.made_new_selection = False

    def user_selection(self, prompt: str, sequence: List[str]) -> int:
        serialized_selections = ";".join(sequence)

        lookup_result = self.lookup_selection(prompt, serialized_selections)
        if lookup_result:
            logger.debug(f"Using previously supplied answer '{lookup_result}' to prompt '{prompt}'")
            return sequence.index(lookup_result)

        self.made_new_selection = True

        print(prompt)
        for idx, s in enumerate(sequence):
            print(f" [{idx}]: {s}")
        selection = input("")
        while not try_parse_int(selection):
            selection = input("Invalid, try again: ")
        selected_index = int(selection)

        self.selections.append(
            {
                "prompt": prompt,
                "sequence": serialized_selections,
                "selection": sequence[selected_index],
            }
        )
        return selected_index

    def lookup_selection(self, prompt: str, serialized_sequence: str) -> Union[str, None]:
        hits = [
            record
            for record in self.selections
            if record["prompt"] == prompt and record["sequence"] == serialized_sequence
        ]
        if len(hits) == 0:
            return None
        elif len(hits) > 1:
            msg = f"Found multiple records for query {prompt} with selections {serialized_sequence}"
            logger.warn(msg)
            idx = self.user_selection(msg, [h["selection"] for h in hits])
            return hits[idx]["selection"]
        else:
            return hits[0]["selection"]

    def record_selections(self, filename: Optional[str] = None):
        if not filename:
            filename = f"selections_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"

        if len(self.selections) > 0 and self.made_new_selection:
            with open(filename, "w") as f:
                writer = csv.DictWriter(f, self.selections[0].keys())
                writer.writeheader()
                writer.writerows(self.selections)
            logger.info(f"Wrote user selections to {filename}. They can be reused with the '-s' flag")
        else:
            logger.debug("There were no user selections to record.")

    def import_selections(self, filename: str):
        logger.info(f"Importing selections file {filename}")
        with open(filename, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "prompt" in row and "sequence" in row and "selection" in row:
                    self.selections.append(row)
                else:
                    logger.warn(
                        f"Imported selection missing one or more of the expected members and will not be imported: {row}"
                    )


user_selector = UserSelection()

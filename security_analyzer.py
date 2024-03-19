#!/usr/bin/python3
# PYTHON_ARGCOMPLETE_OK
import argparse
import argcomplete
from argcomplete.completers import FilesCompleter
from datetime import datetime

from qualified_dividends_analyzer import analyze_qualified_dividends
from utilities.config import configure_logger
from utilities.user_selection import user_selector


def main():
    arg_parser = argparse.ArgumentParser(
        prog='security_analyzer',
        description='Tax tool for analyzing various aspects of securities')

    csv_completer = FilesCompleter(("csv"))
    arg_parser.add_argument("-s", "--selections", nargs="?", action="store",
        help=(
            "A CSV file of user selections generated from a previous"
            " run which will automatically be applied where applicable"
        )).completer = csv_completer  # type: ignore

    subparsers = arg_parser.add_subparsers(required=True, help="subcommands")

    exdate_parser = subparsers.add_parser(
        "dividends", help="Analyze dividend exdates and closed lots to properly classify qualified dividends")
    exdate_parser.add_argument(
        "-l", "--lots", nargs="+", action='append', required=True,
        help="CSV files that contain the necessary information about closed lots"
    ).completer = csv_completer  # type: ignore
    exdate_parser.add_argument("-d", "--dividends", nargs="+", action='append', required=True,
        help="CSV files that contain the necessary information about dividends"
    ).completer = csv_completer  # type: ignore
    exdate_parser.add_argument("-y", "--year", nargs=1, action='store', required=False,
        default=datetime.now().year - 1,
        help="The year for which to look up dividend information. Defaults to the previous year"
    )

    exdate_parser.set_defaults(func=analyze_qualified_dividends)

    argcomplete.autocomplete(arg_parser)

    args = arg_parser.parse_args()

    # order matter -- only configure the logger if we're about to delegate to a subcommand
    configure_logger()

    if args.selections:
        user_selector.import_selections(args.selections)

    args.func(args)

    user_selector.record_selections()


if __name__ == "__main__":
    main()

#!/usr/bin/python3
# PYTHON_ARGCOMPLETE_OK
import argparse
import argcomplete
from argcomplete.completers import FilesCompleter
from datetime import datetime

from qualified_dividends_analyzer import analyze_qualified_dividends
from summarizer import summarize
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

    qualified_dividends_analyzer = subparsers.add_parser(
        "dividends", help="Analyze dividend exdates and closed lots to properly classify qualified dividends")
    qualified_dividends_analyzer.add_argument(
        "-l", "--lots", nargs="+", action='append', required=True, metavar="lots.csv",
        help="CSV files that contain the necessary information about closed lots. May be specified multiple times"
    ).completer = csv_completer  # type: ignore
    qualified_dividends_analyzer.add_argument("-d", "--dividends", nargs="+", action='append', required=True, metavar="divs.csv",
        help="CSV files that contain the necessary information about dividends. May be specified multiple times."
    ).completer = csv_completer  # type: ignore
    qualified_dividends_analyzer.add_argument("-y", "--year", nargs=1, action='store', required=False,
        default=datetime.now().year - 1,
        help="The year for which to look up dividend information. Defaults to the previous year"
    )
    qualified_dividends_analyzer.set_defaults(func=analyze_qualified_dividends)

    summerizer_parser = subparsers.add_parser(
        "summarize", help="Produce summaries akin to the 1099 summary information table")
    summerizer_parser.add_argument(
        "-l", "--lots", nargs="+", action='append', required=False, metavar="lots.csv",
        help="CSV files that contain the necessary information about closed lots. May be specified multiple times"
    ).completer = csv_completer  # type: ignore
    summerizer_parser.add_argument("-d", "--dividends", nargs="+", action='append', required=False, metavar="divs.csv",
        help="CSV files that contain the necessary information about dividends. May be specified multiple times."
    ).completer = csv_completer  # type: ignore
    summerizer_parser.set_defaults(func=summarize)

    argcomplete.autocomplete(arg_parser)

    args = arg_parser.parse_args()

    # order matter -- only configure the logger if we're about to delegate to a subcommand
    configure_logger()

    if args.selections:
        user_selector.import_selections(args.selections)

    try:
        args.func(args)
    finally:
        if args.selections:
            user_selector.record_selections(args.selections)
        else:
            user_selector.record_selections()


if __name__ == "__main__":
    main()

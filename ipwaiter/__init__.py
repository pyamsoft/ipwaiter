#!/usr/bin/env python3

import argparse

from ._version import __version__


def _initialize_parser():
    """Set up the option parser with the options we handle"""
    parser = argparse.ArgumentParser(prog="ipwaiter")

    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s {}".format(__version__),
        help="Display the version and exit")
    parser.add_argument(
        "-R", "--raw",
        action="store_const",
        dest="raw",
        const=True,
        help="Operate on RAW orders only")
    parser.add_argument(
        "-A", "--add",
        action="store",
        dest="add",
        nargs=2,
        metavar=("ORDER", "CHAIN"),
        help="Add the ORDER to the CHAIN")
    parser.add_argument(
        "-D", "--delete",
        action="store",
        dest="delete",
        nargs=2,
        metavar=("ORDER", "CHAIN"),
        help="Delete the ORDER from the CHAIN")
    return parser


def _parse_options():
    parser = _initialize_parser()
    parsed = parser.parse_args()
    print(parsed)


def main():
    # Parse the options before starting setup
    _parse_options()

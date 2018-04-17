#!/usr/bin/env python3

import argparse
import os
import sys

from .iptables.iptables import Iptables
from .logger.logger import Logger
from .orders.lister import ListOrders
from .orders.waiter import Waiter
from .orders.systemconf import SystemConfParser
from ._version import __version__


def _initialize_parser():
    """Set up the option parser with the options we handle"""
    parser = argparse.ArgumentParser(prog="ipwaiter")

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Display the version and exit")
    parser.add_argument(
        "-R", "--raw",
        action="store_const",
        dest="raw",
        const=True,
        help="Operate on RAW orders only")
    parser.add_argument(
        "-L", "--list",
        action="store_const",
        dest="list_orders",
        const=True,
        help="List all orders")
    parser.add_argument(
        "-H", "--hire",
        action="store_const",
        dest="hire",
        const=True,
        help="Runs all the orders listed in system.conf")
    parser.add_argument(
        "-F", "--fire",
        action="store_const",
        dest="fire",
        const=True,
        help="Removes all the orders listed in system.conf")
    parser.add_argument(
        "--rehire",
        action="store_const",
        dest="rehire",
        const=True,
        help="Fires the old waiter and Hires a new one")
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
    parser.add_argument(
        "--dir",
        action="store",
        dest="orders",
        metavar="DIR",
        help="Directory with all the ORDER files")
    parser.add_argument(
        "-s", "--src",
        action="store",
        dest="src",
        metavar="SRC",
        help="Source IP address block for orders")
    parser.add_argument(
        "-d", "--dst",
        action="store",
        dest="dst",
        metavar="DST",
        help="Destination IP address block for orders")
    return parser


def _parse_options():
    parser = _initialize_parser()
    parsed = parser.parse_args()

    # If nothing at all was picked, show help
    if (not parsed.delete and not parsed.add and
            not parsed.hire and not parsed.fire and not parsed.rehire and
            not parsed.list_orders):
        parser.print_help()
        sys.exit(0)

    return parsed


def _exit_if_not_super():
    if os.geteuid() != 0:
        Logger.fatal("You must be root to use ipwaiter")


def main():
    # Parse the options before starting setup
    parsed = _parse_options()

    # We must have superuser privs
    _exit_if_not_super()

    # Set or override the order_dir
    order_dir = "/etc/ipwaiter/orders"
    if parsed.orders:
        order_dir = parsed.orders

    if parsed.add and parsed.delete:
        Logger.log("Must specify only one of either --add or --delete")
        sys.exit(1)

    if (parsed.hire and parsed.fire) or (parsed.rehire and parsed.hire) \
            or (parsed.fire and parsed.rehire):
        Logger.log("Must specify only one of either --fire or --hire or --rehire")
        sys.exit(1)

    opts = {}
    if parsed.src:
        opts["src"] = parsed.src
    if parsed.dst:
        opts["dst"] = parsed.dst

    iptables = Iptables()
    system_conf = SystemConfParser("/etc/ipwaiter/system.conf")
    if parsed.add:
        Waiter(iptables, order_dir, system_conf).add_order(parsed.add, parsed.raw, opts)
    elif parsed.delete:
        Waiter(iptables, order_dir, system_conf).delete_order(parsed.delete, parsed.raw)
    elif parsed.list_orders:
        ListOrders(order_dir).list_all()
    elif parsed.hire:
        Waiter(iptables, order_dir, system_conf).hire_waiter(opts)
    elif parsed.fire:
        Waiter(iptables, order_dir, system_conf).fire_waiter()
    elif parsed.rehire:
        Waiter(iptables, order_dir, system_conf).rehire_waiter(opts)
    else:
        Logger.fatal("Reached the end of the script without a valid command!")

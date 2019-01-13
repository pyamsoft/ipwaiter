#!/usr/bin/env python3
#
#  The GPLv2 License
#
#    Copyright (C) 2019  Peter Kenji Yamanaka
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import argparse
import os
import sys

from .constants import PathConstants
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
        "-T", "--teardown",
        action="store_const",
        dest="teardown",
        const=True,
        help="Completely removes all orders")
    parser.add_argument(
        "--rehire",
        action="store_const",
        dest="rehire",
        const=True,
        help="Fires the old waiter and Hires a new one")
    parser.add_argument(
        "--debug",
        action="store_const",
        dest="debug",
        const=True,
        help="Enable runtime debugging")
    parser.add_argument(
        "-A", "--add",
        action="store",
        dest="add",
        nargs="*",
        metavar=("CHAIN", "ORDER"),
        help="Add the ORDER to the CHAIN")
    parser.add_argument(
        "-D", "--delete",
        action="store",
        dest="delete",
        nargs="*",
        metavar=("CHAIN", "ORDER"),
        help="Delete the ORDER from the CHAIN")
    parser.add_argument(
        "-O", "--orders",
        action="append",
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

    if parsed.debug:
        Logger.enabled = True
        Logger.d("Runtime debugging turned on.")

    # If nothing at all was picked, show help
    if (not parsed.delete and not parsed.add and
            not parsed.hire and not parsed.fire and
            not parsed.rehire and not parsed.teardown and
            not parsed.list_orders):
        parser.print_help()
        sys.exit(0)

    return parsed


def _find_config_dir():
    """Find the config directory either from arguments or environment"""
    config_dir = None
    try:
        xdg_env = os.environ[PathConstants.ENV_XDG_CONFIG]
        if xdg_env:
            config_dir = f"{xdg_env}/ipwaiter/orders"
            Logger.d(f"Config dir from {PathConstants.ENV_XDG_CONFIG}: {config_dir}")
    except KeyError:
        Logger.e(f"Error getting config dir from {PathConstants.ENV_XDG_CONFIG}")

        # Set to nothing so it will be handled by next if
        config_dir = None

    # Or from default
    if not config_dir:
        config_dir = os.path.expanduser(PathConstants.HOME_CONFIG_DIR)
        Logger.d(f"Config dir from fallback: {config_dir}")

    return config_dir


def _append_order_dir_if_valid(order_dirs, dir):
    """Append a possible order dir if it is valid"""
    if os.path.isdir(dir):
        order_dirs.append(dir)


def _exit_if_not_super():
    if os.geteuid() != 0:
        Logger.fatal("You must be root to use ipwaiter")


def main():
    # Parse the options before starting setup
    parsed = _parse_options()

    # Orders are searched in system and user config directories
    order_dirs = []
    _append_order_dir_if_valid(order_dirs, PathConstants.SYSTERM_CONFIG_DIR)
    _append_order_dir_if_valid(order_dirs, _find_config_dir())

    # Add any command line arguments to the directories
    if parsed.orders:
        for order_dir in parsed.orders:
            _append_order_dir_if_valid(order_dirs, order_dir)

    # Reverse the list so it will search custom locations and then the home and system last
    order_dirs.reverse()

    if parsed.list_orders:
        ListOrders(order_dirs).list_all()
    else:
        # We must have superuser privs
        _exit_if_not_super()

        if parsed.add and parsed.delete:
            Logger.log("Must specify only one of either --add or --delete")
            sys.exit(1)

        if (parsed.hire and parsed.fire) or (parsed.rehire and parsed.hire) \
                or (parsed.fire and parsed.rehire):
            Logger.log("Must specify only one of either "
                       "--fire or --hire or --rehire")
            sys.exit(1)

        opts = {}
        if parsed.src:
            opts["src"] = parsed.src
        if parsed.dst:
            opts["dst"] = parsed.dst

        iptables = Iptables()
        system_conf = SystemConfParser("/etc/ipwaiter/system.conf")
        waiter = Waiter(iptables, order_dirs, system_conf)

        if parsed.add:
            waiter.add_order(parsed.add, parsed.raw, opts)
        elif parsed.delete:
            waiter.delete_order(parsed.delete, parsed.raw)
        elif parsed.hire:
            waiter.hire_waiter(opts=opts, report=parsed.debug)
        elif parsed.fire or parsed.teardown:
            waiter.fire_waiter(destroy=parsed.teardown, report=parsed.debug)
        elif parsed.rehire:
            waiter.rehire_waiter(opts=opts, report=parsed.debug)
        else:
            Logger.fatal("Reached the end of the script without a valid command!")

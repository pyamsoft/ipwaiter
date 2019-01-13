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


import os

import ipwaiter.utils as utils

from ..logger.logger import Logger


class Preconditions:

    def __init__(self, iptables, order_dirs, raw):
        for order_dir in order_dirs:
            if not os.path.isdir(order_dir):
                Logger.fatal(f"Invalid order directory: {order_dir}")

        if not iptables:
            Logger.fatal(f"Invalid iptables handler given: {iptables}")

        self._iptables = iptables
        self._order_dirs = order_dirs
        self._raw = raw

    def create_chains_if_needed(self):
        if self._raw:
            if not self._iptables.exists("raw", "output_orders"):
                self._iptables.create("raw", "output_orders")
        else:
            if not self._iptables.exists("filter", "input_orders"):
                self._iptables.create("filter", "input_orders")
            if not self._iptables.exists("filter", "forward_orders"):
                self._iptables.create("filter", "forward_orders")
            if not self._iptables.exists("filter", "output_orders"):
                self._iptables.create("filter", "output_orders")

    def valid_chain(self, chain):
        if not chain:
            Logger.fatal(f"Invalid chain, cannot check: {chain}")

        # Compare the upper case input
        uppercase = chain.upper()

        # Transform the real chain name
        chain = f"{chain.lower()}_orders"
        if self._raw:
            return chain if uppercase in ["OUTPUT"] else ""
        else:
            return chain if uppercase in ["INPUT", "FORWARD", "OUTPUT"] else ""

    def valid_order(self, order):
        if not order:
            Logger.fatal(f"Invalid order, cannot check: {order}")

        for order_dir in self._order_dirs:
            for file in os.listdir(order_dir):
                abspath = utils.to_absolute_path(order_dir, file)
                if (os.path.isfile(abspath) and abspath.endswith(".order")
                        and os.path.basename(file) == f"{order}.order"):
                    return abspath

        return ""

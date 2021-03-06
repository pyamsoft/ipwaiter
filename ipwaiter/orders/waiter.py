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
import re
import shlex

import ipwaiter.utils as utils

from ..iptables.preconditions import Preconditions
from ..logger.logger import Logger
from .reader import OrderReader


class Waiter:

    def __init__(self, iptables, order_dirs, system_conf):
        for order_dir in order_dirs:
            if not os.path.isdir(order_dir):
                Logger.fatal(f"Invalid order directory given: {order_dir}")

        if not iptables:
            Logger.fatal(f"Invalid iptables handler given: {iptables}")

        self._system_conf = system_conf
        self._order_dirs = order_dirs
        self._iptables = iptables

    def _verify(self, name, raw, chain):
        preconditions = Preconditions(self._iptables, self._order_dirs, raw)

        # Create the required chains
        preconditions.create_chains_if_needed()

        order = preconditions.valid_order(name)
        if not order:
            Logger.fatal(f"Verify failed invalid order: {name}")

        parent = preconditions.valid_chain(chain)
        if not parent:
            Logger.fatal(f"Verify failed invalid chain: {chain}")

        chain = f"order_{name}"
        table = "raw" if raw else "filter"

        return name, table, chain, parent, order

    def add_order(self, order, raw, opts):
        self._add_order(order, raw, opts, report=True)

    def _add_order(self, order, raw, opts, report):
        if not order:
            Logger.fatal("Cannot add empty order")

        o_chain = order[0]
        o_names = order[1:]

        for o_name in o_names:
            o_name = o_name.strip()
            verified = self._verify(o_name, raw, o_chain)
            name, table, chain, parent, path = verified
            self._place_order(name, table, chain, parent,
                              path, raw, opts, report)

    def _place_order(self, name, table, chain, parent,
                     path, raw, opts, report):
        if report:
            Logger.log(f"ipwaiter is placing order: {name}")

        # Create the chain first
        if not self._iptables.exists(table, chain):
            if not self._iptables.create(table, chain):
                if report:
                    Logger.fatal(f"Failed to create chain: {chain} for "
                                 f"table: {table}")

        # Add all of the rules for the
        reader = OrderReader(path, opts)
        for (read_table, read_line) in reader.as_lines():

            # Read line is a simple split string, but cannot
            # handle embedded quotes inside of strings.
            # Join it into a string again, and re-split
            # it with shlex for better handling
            read_line = " ".join(read_line)
            read_line = shlex.split(read_line)

            if ((raw and read_table == "raw") or
                    (not raw and read_table == "filter")):
                # Add rule if needed
                if not self._iptables.check_add(read_table, chain, read_line):
                    if not self._iptables.add(read_table, chain, read_line):
                        if report:
                            Logger.fatal(f"Failed add. table {read_line}, "
                                         f"chain {chain}, rule {read_line}")

        # Link the new chain to the parent chain
        if self._iptables.check_link(table, parent, chain):
            if report:
                Logger.log(f"ipwaiter has already placed order: {name}")
            return
        else:
            if not self._iptables.link(table, parent, chain):
                if report:
                    Logger.fatal(f"Failed to link chain: {chain} "
                                 f"table: {table} to: {parent}")

        if report:
            Logger.log(f"ipwaiter has placed order: {name}")

    def delete_order(self, order, raw):
        self._delete_order(order, raw, report=True, destroy=False)

    def _delete_order(self, order, raw, report, destroy):
        if not order:
            Logger.fatal("Cannot delete empty order")

        o_chain = order[0]
        o_names = order[1:]

        for o_name in o_names:
            o_name = o_name.strip()
            verified = self._verify(o_name, raw, o_chain)
            name, table, chain, parent, path = verified
            self._remove_order(name, table, chain, parent, report, destroy)

    def _remove_order(self, name, table, chain, parent, report, destroy):
        # Stop if the chain does not exist
        if not self._iptables.exists(table, chain):
            if report:
                Logger.log(f"ipwaiter has never placed order: {name}")
            return

        if report:
            Logger.log(f"ipwaiter is removing order: {name}")

        # Make sure we can work
        if not self._iptables.check_link(table, parent, chain):
            if report:
                Logger.log(f"ipwaiter has never placed order: {name}")
            return

        # Unlink the chain first
        if not self._iptables.unlink(table, parent, chain):
            if report:
                Logger.fatal(f"Failed to unlink chain: {chain} table: "
                             f"{table} from: {parent}")
            return

        # If we are tearing down
        if destroy:
            if not self._iptables.flush(table, chain):
                if report:
                    Logger.fatal(f"Failed to flush chain: {chain} "
                                 f"table: {table}")
                return

            if not self._iptables.delete(table, chain):
                if report:
                    Logger.fatal(f"Failed to delete chain: {chain} "
                                 f"table: {table}")
                return

        if report:
            Logger.log(f"ipwaiter has removed order: {name}")

    def hire_waiter(self, opts, report):
        Logger.log("Hiring new ipwaiter")
        order_dict = self._system_conf.parse()

        orders = order_dict["FILTER_INPUT"]
        if orders:
            self._add_order(("input", *orders),
                            raw=False, opts=opts, report=report)

        orders = order_dict["FILTER_FORWARD"]
        if orders:
            self._add_order(("forward", *orders),
                            raw=False, opts=opts, report=report)

        orders = order_dict["FILTER_OUTPUT"]
        if orders:
            self._add_order(("output", *orders),
                            raw=False, opts=opts, report=report)

        orders = order_dict["RAW_OUTPUT"]
        if orders:
            self._add_order(("output", *orders),
                            raw=True, opts=opts, report=report)

        Logger.log("Hired ipwaiter")

    def fire_waiter(self, destroy, report):
        Logger.log("Firing old ipwaiter")

        orders = []
        if destroy:
            for order_dir in self._order_dirs:
                for order in os.listdir(order_dir):
                    abspath = utils.to_absolute_path(order_dir, order)
                    if os.path.isfile(abspath) and abspath.endswith(".order"):
                        base_order = os.path.basename(abspath)
                        base_order = re.sub(r"\.order$", "", base_order)
                        orders.append(base_order)

        # Delete all not raw
        if destroy:
            self._delete_order(("input", *orders),
                               raw=False, report=report, destroy=True)
            self._delete_order(("forward", *orders),
                               raw=False, report=report, destroy=True)
            self._delete_order(("output", *orders),
                               raw=False, report=report, destroy=True)

            # Delete all raw
            self._delete_order(("output", *orders),
                               raw=True, report=report, destroy=True)

        # Delete the order chains
        self._iptables.flush("filter", "input_orders")
        self._iptables.flush("filter", "forward_orders")
        self._iptables.flush("filter", "output_orders")
        self._iptables.flush("raw", "output_orders")

        if destroy:
            self._iptables.delete("filter", "input_orders")
            self._iptables.delete("filter", "forward_orders")
            self._iptables.delete("filter", "output_orders")
            self._iptables.delete("raw", "output_orders")

        Logger.log("Fired ipwaiter")

    def rehire_waiter(self, opts, report):
        self.fire_waiter(destroy=False, report=report)
        self.hire_waiter(opts=opts, report=report)

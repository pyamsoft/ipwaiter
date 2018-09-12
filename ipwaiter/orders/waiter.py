#!/usr/bin/env python3

import os
import re
import shlex

import ipwaiter.utils as utils

from ..iptables.preconditions import Preconditions
from ..logger.logger import Logger
from .reader import OrderReader


class Waiter:

    def __init__(self, iptables, order_dir, system_conf):
        if not os.path.isdir(order_dir):
            Logger.fatal(f"Invalid order directory given: {order_dir}")

        if not iptables:
            Logger.fatal(f"Invalid iptables handler given: {iptables}")

        self._system_conf = system_conf
        self._order_dir = order_dir
        self._iptables = iptables

    def _verify(self, name, raw, chain):
        preconditions = Preconditions(self._iptables, self._order_dir, raw)

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
            name, table, chain, parent, path = self._verify(o_name, raw, o_chain)
            self._place_order(name, table, chain, parent, path, raw, opts, report)

    def _place_order(self, name, table, chain, parent, path, raw, opts, report):
        # Stop if the chain exists
        if self._iptables.exists(table, chain):
            if report:
                Logger.log(f"ipwaiter has already placed order: {name}")
            return

        if report:
            Logger.log(f"ipwaiter is placing order: {name}")

        # Create the chain first
        if not self._iptables.create(table, chain):
            if report:
                Logger.fatal(f"Failed to create chain: {chain} for table: {table}")

        # Add all of the rules for the
        reader = OrderReader(path, opts)
        for (read_table, read_line) in reader.as_lines():

            # Read line is a simple split string, but cannot handle embedded quotes inside of strings.
            # Join it into a string again, and re-split it with shlex for better handling
            read_line = " ".join(read_line)
            read_line = shlex.split(read_line)

            if ((raw and read_table == "raw") or
                    (not raw and read_table == "filter")):
                if not self._iptables.add(read_table, chain, read_line):
                    if report:
                        Logger.fatal(f"Failed add. table {read_line}, chain {chain}, rule {read_line}")

        # Link the new chain to the parent chain
        if not self._iptables.link(table, parent, chain):
            if report:
                Logger.fatal(f"Failed to link chain: {chain} table: {table} to: {parent}")

        if report:
            Logger.log(f"ipwaiter has placed order: {name}")

    def delete_order(self, order, raw):
        self._delete_order(order, raw, report=True)

    def _delete_order(self, order, raw, report):
        if not order:
            Logger.fatal("Cannot delete empty order")

        o_chain = order[0]
        o_names = order[1:]

        for o_name in o_names:
            o_name = o_name.strip()
            name, table, chain, parent, path = self._verify(o_name, raw, o_chain)
            self._remove_order(name, table, chain, parent, report)

    def _remove_order(self, name, table, chain, parent, report):
        # Stop if the chain does not exist
        if not self._iptables.exists(table, chain):
            if report:
                Logger.log(f"ipwaiter has never placed order: {name}")
            return

        if report:
            Logger.log(f"ipwaiter is removing order: {name}")

        # Unlink the chain first so we know its valid
        if not self._iptables.unlink(table, parent, chain):
            if report:
                Logger.fatal(f"Failed to unlink chain: {chain} table: {table} from: {parent}")
            else:
                return

        # Flush the chain second
        if not self._iptables.flush(table, chain):
            if report:
                Logger.fatal(f"Failed to flush chain: {chain} for table: {table}")
            else:
                return

        # Then delete the chain
        if not self._iptables.delete(table, chain):
            if report:
                Logger.fatal(f"Failed to delete chain: {chain} for table: {table}")
            else:
                return

        if report:
            Logger.log(f"ipwaiter has removed order: {name}")

    def hire_waiter(self, opts):
        Logger.log("Hiring new ipwaiter")
        order_dict = self._system_conf.parse()

        orders = order_dict["FILTER_INPUT"]
        if orders:
            self._add_order(("input", orders), raw=False, opts=opts, report=False)

        orders = order_dict["FILTER_FORWARD"]
        if orders:
            self._add_order(("forward", orders), raw=False, opts=opts, report=False)

        orders = order_dict["FILTER_OUTPUT"]
        if orders:
            self._add_order(("output", orders), raw=False, opts=opts, report=False)

        orders = order_dict["RAW_OUTPUT"]
        if orders:
            self._add_order(("output", orders), raw=True, opts=opts, report=False)

        Logger.log("Hired ipwaiter")

    def fire_waiter(self):
        Logger.log("Firing old ipwaiter")

        orders = []
        for order in os.listdir(self._order_dir):
            abspath = utils.to_absolute_path(self._order_dir, order)
            if os.path.isfile(abspath) and abspath.endswith(".order"):
                base_order = os.path.basename(abspath)
                base_order = re.sub("\.order$", "", base_order)
                orders.append(base_order)

        # Delete all not raw
        self._delete_order(("input", orders), raw=False, report=False)
        self._delete_order(("forward", orders), raw=False, report=False)
        self._delete_order(("output", orders), raw=False, report=False)

        # Delete all raw
        self._delete_order(("output", orders), raw=True, report=False)

        # Delete the order chains
        self._iptables.flush("filter", "input_orders")
        self._iptables.flush("filter", "forward_orders")
        self._iptables.flush("filter", "output_orders")
        self._iptables.delete("filter", "input_orders")
        self._iptables.delete("filter", "forward_orders")
        self._iptables.delete("filter", "output_orders")

        self._iptables.flush("raw", "output_orders")
        self._iptables.delete("raw", "output_orders")

        Logger.log("Fired ipwaiter")

    def rehire_waiter(self, opts):
        self.fire_waiter()
        self.hire_waiter(opts)

#!/usr/bin/env python3

import os
import re

import ipwaiter.utils as utils

from ..iptables.preconditions import Preconditions
from ..logger.logger import Logger
from .reader import OrderReader


class Waiter:

    def __init__(self, iptables, order_dir):
        if not os.path.isdir(order_dir):
            Logger.fatal("Invalid order directory given: {}".format(order_dir))

        if not iptables:
            Logger.fatal("Invalid iptables handler given: {}".format(iptables))

        self._order_dir = order_dir
        self._iptables = iptables

    def _verify(self, name, raw, chain):
        preconditions = Preconditions(self._iptables, self._order_dir, raw)

        # Create the required chains
        preconditions.create_chains_if_needed()

        order = preconditions.valid_order(name)
        if not order:
            Logger.fatal("Verify failed invalid order: {}".format(name))

        parent = preconditions.valid_chain(chain)
        if not parent:
            Logger.fatal("Verify failed invalid chain: {}".format(chain))

        chain = "order_{}".format(name)
        table = "raw" if raw else "filter"

        return name, table, chain, parent, order

    def add_order(self, order, raw, opts):
        self._add_order(order, raw, opts, True)

    def _add_order(self, order, raw, opts, report):
        if not order:
            Logger.fatal("Cannot add empty order")

        o_name = order[1]
        o_chain = order[0]

        name, table, chain, parent, path = self._verify(o_name, raw, o_chain)
        self._place_order(name, table, chain, parent, path, raw, opts, report)

    def _place_order(self, name, table, chain, parent, path, raw, opts, report):
        # Stop if the chain exists
        if self._iptables.exists(table, chain):
            if report:
                Logger.log("ipwaiter has already placed order: {}".format(name))
            return

        if report:
            Logger.log("ipwaiter is placing order: {}".format(name))

        # Create the chain first
        if not self._iptables.create(table, chain):
            if report:
                Logger.fatal("Failed to create chain: {} for table: {}"
                             .format(chain, table))

        # Add all of the rules for the
        reader = OrderReader(path, opts)
        for (read_table, read_line) in reader.as_lines():

            if ((raw and read_table == "raw") or
                    (not raw and read_table == "filter")):
                if not self._iptables.add(read_table, chain, read_line):
                    if report:
                        Logger.fatal("Failed add. table {}, chain {}, rule {}"
                                     .format(read_table, chain, read_line))

        # Link the new chain to the parent chain
        if not self._iptables.link(table, parent, chain):
            if report:
                Logger.fatal("Failed to link chain: {} table: {} to: {}"
                             .format(chain, table, parent))

        if report:
            Logger.log("ipwaiter has placed order: {}".format(name))

    def delete_order(self, order, raw):
        self._delete_order(order, raw, True)

    def _delete_order(self, order, raw, report):
        if not order:
            Logger.fatal("Cannot delete empty order")

        o_name = order[1]
        o_chain = order[0]
        name, table, chain, parent, path = self._verify(o_name, raw, o_chain)
        self._remove_order(name, table, chain, parent, report)

    def _remove_order(self, name, table, chain, parent, report):
        # Stop if the chain does not exist
        if not self._iptables.exists(table, chain):
            if report:
                Logger.log("ipwaiter has never placed order: {}".format(name))
            return

        if report:
            Logger.log("ipwaiter is removing order: {}".format(name))

        # Unlink the chain first so we know its valid
        if not self._iptables.unlink(table, parent, chain):
            if report:
                Logger.fatal("Failed to unlink chain: {} table: {} from: {}"
                             .format(chain, table, parent))
            else:
                return

        # Flush the chain second
        if not self._iptables.flush(table, chain):
            if report:
                Logger.fatal("Failed to flush chain: {} for table: {}"
                             .format(chain, table))
            else:
                return

        # Then delete the chain
        if not self._iptables.delete(table, chain):
            if report:
                Logger.fatal("Failed to delete chain: {} for table: {}"
                             .format(chain, table))
            else:
                return

        if report:
            Logger.log("ipwaiter has removed order: {}".format(name))

    def hire_waiter(self):
        Logger.log("Hire waiter")

    def fire_waiter(self):
        Logger.log("Firing old ipwaiter")

        for order in os.listdir(self._order_dir):
            abspath = utils.to_absolute_path(self._order_dir, order)
            if os.path.isfile(abspath) and abspath.endswith(".order"):
                base_order = os.path.basename(abspath)
                base_order = re.sub("\.order$", "", base_order)

                # Delete all not raw
                self._delete_order(("input", base_order), False, False)
                self._delete_order(("forward", base_order), False, False)
                self._delete_order(("output", base_order), False, False)

                # Delete all raw
                self._delete_order(("output", base_order), True, False)

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

    def rehire_waiter(self):
        self.fire_waiter()
        self.hire_waiter()

#!/usr/bin/env python3

import os

from ..iptables.iptables import Iptables
from ..iptables.preconditions import Preconditions
from ..logger.logger import Logger
from .reader import OrderReader


class Waiter:

    def __init__(self, order_dir):
        if not os.path.isdir(order_dir):
            Logger.fatal("Invalid order directory given: {}".format(order_dir))
        self._order_dir = order_dir
        self._iptables = Iptables()

    def _verify(self, name, raw, chain):
        preconditions = Preconditions(self._order_dir, raw)

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
        if not order:
            Logger.fatal("Cannot add empty order")

        o_name = order[1]
        o_chain = order[0]

        name, table, chain, parent, path = self._verify(o_name, raw, o_chain)
        self._place_order(name, table, chain, parent, path, raw, opts)

    def _place_order(self, name, table, chain, parent, path, raw, opts):
        # Stop if the chain exists
        if self._iptables.exists(table, chain):
            Logger.log("ipwaiter has already placed order: {}".format(name))
            return

        Logger.log("ipwaiter is placing order: {}".format(name))

        # Create the chain first
        if not self._iptables.create(table, chain):
            Logger.fatal("Failed to create chain: {} for table: {}"
                         .format(chain, table))

        # Add all of the rules for the
        reader = OrderReader(path, opts)
        for (read_table, read_line) in reader.as_lines():

            if ((raw and read_table == "raw") or
                    (not raw and read_table == "filter")):
                if not self._iptables.add(read_table, chain, read_line):
                    Logger.fatal("Failed add. table: {}, chain: {}, rule: {}"
                                 .format(read_table, chain, read_line))

        # Link the new chain to the parent chain
        if not self._iptables.link(table, parent, chain):
            Logger.fatal("Failed to link chain: {} for table: {} to: {}"
                         .format(chain, table, parent))

        Logger.log("ipwaiter has placed order: {}".format(name))

    def delete_order(self, order, raw):
        if not order:
            Logger.fatal("Cannot delete empty order")

        o_name = order[1]
        o_chain = order[0]
        name, table, chain, parent, path = self._verify(o_name, raw, o_chain)
        self._remove_order(name, table, chain, parent)

    def _remove_order(self, name, table, chain, parent):
        # Stop if the chain does not exist
        if not self._iptables.exists(table, chain):
            Logger.log("ipwaiter has never placed order: {}".format(name))
            return

        Logger.log("ipwaiter is removing order: {}".format(name))

        # Flush the chain first
        if not self._iptables.flush(table, chain):
            Logger.fatal("Failed to flush chain: {} for table: {}"
                         .format(chain, table))

        # Unlink the chain second
        if not self._iptables.unlink(table, parent, chain):
            Logger.fatal("Failed to unlink chain: {} for table: {} from: {}"
                         .format(chain, table, parent))

        # Then delete the chain
        if not self._iptables.delete(table, chain):
            Logger.fatal("Failed to delete chain: {} for table: {}"
                         .format(chain, table))

        Logger.log("ipwaiter has removed order: {}".format(name))

    def hire_waiter(self):
        Logger.log("Hire waiter")

    def fire_waiter(self):
        Logger.log("Fire waiter")

    def rehire_waiter(self):
        self.fire_waiter()
        self.hire_waiter()

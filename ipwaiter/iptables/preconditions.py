#!/usr/bin/env python3

import os

import ipwaiter.utils as utils

from ..logger.logger import Logger


class Preconditions:

    def __init__(self, iptables, order_dir, raw):
        if not os.path.isdir(order_dir):
            Logger.fatal("Invalid order directory: {}".format(order_dir))

        if not iptables:
            Logger.fatal("Invalid iptables handler given: {}".format(iptables))

        self._iptables = iptables
        self._order_dir = order_dir
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
            Logger.fatal("Invalid chain, cannot check: {}".format(chain))

        # Compare the upper case input
        uppercase = chain.upper()

        # Transform the real chain name
        chain = "{}_orders".format(chain.lower())
        if self._raw:
            return chain if uppercase in ["OUTPUT"] else ""
        else:
            return chain if uppercase in ["INPUT", "FORWARD", "OUTPUT"] else ""

    def valid_order(self, order):
        if not order:
            Logger.fatal("Invalid order, cannot check: {}".format(order))

        for file in os.listdir(self._order_dir):
            abspath = utils.to_absolute_path(self._order_dir, file)
            if (os.path.isfile(abspath) and abspath.endswith(".order")
                    and os.path.basename(file) == "{}.order".format(order)):
                return abspath

        return ""

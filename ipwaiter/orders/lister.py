#!/usr/bin/env python3

import os

import ipwaiter.utils as utils

from ..logger.logger import Logger
from .reader import OrderReader


class ListOrders:

    def __init__(self, order_dir):
        if not os.path.isdir(order_dir):
            Logger.fatal("Invalid order directory: {}".format(order_dir))
        self._order_dir = order_dir

    def list_all(self):
        counter = 0
        for order in os.listdir(self._order_dir):
            abspath = utils.to_absolute_path(self._order_dir, order)
            if os.path.isfile(abspath) and abspath.endswith(".order"):
                reader = OrderReader(abspath, None)
                content = reader.as_string()
                if content:
                    counter += 1
                    Logger.log("From order: {}".format(order))
                    Logger.log("============================")
                    Logger.log(content)
                    Logger.log("")

        Logger.log("Total order count: {}".format(counter))

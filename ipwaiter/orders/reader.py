#!/usr/bin/env python3

import os

from ..logger.logger import Logger


class OrderReader:

    def __init__(self, path):
        if not os.path.isfile(path):
            Logger.fatal("Invalid order given: {}".format(path))
        self._path = path

    def _get_order(self):
        try:
            order = open(self._path, "r")
        except OSError as e:
            Logger.e("Unable to read order file")
            Logger.e(e)
            return []
        else:
            with order:
                return order.readlines()

    def as_lines(self):
        return self._get_order()

    def as_string(self):
        return "".join(self._get_order())

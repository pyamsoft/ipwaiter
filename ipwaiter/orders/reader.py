#!/usr/bin/env python3

import os

from ..logger.logger import Logger


class OrderReader:

    def __init__(self, path, opts):
        if not os.path.isfile(path):
            Logger.fatal("Invalid order given: {}".format(path))
        self._path = path
        self._opts = opts

    def _get_order(self):
        try:
            order = open(self._path, "r")
        except OSError as e:
            Logger.e("Unable to read order file")
            Logger.e(e)
            return []
        else:
            with order:
                result = []
                for line in order.readlines():
                    # Remove all whitespace
                    line = line.strip()

                    # Make sure this line is not a comment
                    if line and not line.startswith("#"):
                        line = line.split("#", 1)[0]
                        line = line.rstrip()

                        table, line = line.split(" ", 1)
                        table = table.strip()
                        line = line.strip()

                        # Assume a default
                        src = "192.168.1.0/24"
                        dst = "192.168.1.0/24"

                        # Unless we read from reader opts
                        if self._opts:
                            opt_src = self._opts["src"]
                            opt_dst = self._opts["dst"]

                            if opt_src:
                                src = opt_src

                            if opt_dst:
                                dst = opt_dst

                        # Replace placeholder values with real
                        line = line.replace("__ipwaiter_src", src)
                        line = line.replace("__ipwaiter_dst", dst)

                        # We format this so weirdly to make it easier
                        # for waiter.py to consume
                        result.append((table, line.split()))

                return result

    def as_lines(self):
        return self._get_order()

    def as_string(self):
        result = ""
        for (table, line) in self._get_order():
            # Because the format is so weird for these lines so that
            # waiter.py can consume it easier, we have to do a lot of
            # manual massaging to get them to be display friendly
            args = ""
            for item in line:
                args += "{} ".format(item)
            args += "\n"
            result += "{}: {}".format(table.upper(), args)
        return result

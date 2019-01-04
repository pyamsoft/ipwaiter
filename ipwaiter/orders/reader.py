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

from ..logger.logger import Logger


class OrderReader:

    def __init__(self, path, opts):
        if not os.path.isfile(path):
            Logger.fatal(f"Invalid order given: {path}")
        self._path = path
        self._opts = opts

    def _get_order(self):
        try:
            order = open(self._path, "r")
        except OSError as e:
            Logger.e("Unable to read order file")
            Logger.e(e)
            yield ("", "")
        else:
            with order:
                line = order.readline()
                while line:
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
                        yield (table, line.split())
                    line = order.readline()

    def as_lines(self):
        return self._get_order()

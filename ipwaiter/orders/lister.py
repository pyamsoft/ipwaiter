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
from .reader import OrderReader


class ListOrders:

    def __init__(self, order_dir):
        if not os.path.isdir(order_dir):
            Logger.fatal(f"Invalid order directory: {order_dir}")
        self._order_dir = order_dir

    def list_all(self):
        counter = 0
        for order in os.listdir(self._order_dir):
            abspath = utils.to_absolute_path(self._order_dir, order)
            if os.path.isfile(abspath) and abspath.endswith(".order"):
                reader = OrderReader(abspath, None)

                counter += 1
                Logger.log(f"From order: {order}")
                Logger.log("============================")
                for (table, line) in reader.as_lines():
                    args = ""
                    for item in line:
                        args += f"{item} "
                    args += "\n"
                    Logger.log(f"{table.upper()}: {args}", end="")
                Logger.log("")

        Logger.log(f"Total order count: {counter}")

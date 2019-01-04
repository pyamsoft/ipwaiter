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


class SystemConfParser:

    def __init__(self, path):
        if not os.path.isfile(path):
            Logger.fatal(f"Invalid system conf path given: {path}")
        self._path = path

    def _read_conf(self):
        if self._path is None:
            raise RuntimeError("Cannot call _read_conf() with invalid path")

        try:
            src = open(self._path, mode="r")
        except OSError as e:
            Logger.e(f"Cannot read content from path: {self._path}")
            Logger.e(e)
            yield ""
        else:
            with src:
                line = src.readline()
                while line:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        yield line
                    line = src.readline()

    @staticmethod
    def _grab_content_between_quotes(line):
        items = line.split('"')[1]
        if items:
            return items.split()
        else:
            return []

    @staticmethod
    def _attempt_populate_list(token, line):
        if line.startswith(token):
            stripped = line.strip(token)
            return SystemConfParser._grab_content_between_quotes(stripped)
        else:
            return []

    def parse(self):
        filter_input = []
        filter_forward = []
        filter_output = []
        raw_output = []

        populate_list = SystemConfParser._attempt_populate_list
        for line in self._read_conf():
            # If we are not filled yet, try this line
            if not filter_input:
                filter_input = populate_list("FILTER_INPUT=", line)

            # If we are not filled yet, try this line
            if not filter_forward:
                filter_forward = populate_list("FILTER_FORWARD=", line)

            # If we are not filled yet, try this line
            if not filter_output:
                filter_output = populate_list("FILTER_OUTPUT=", line)

            # If we are not filled yet, try this line
            if not raw_output:
                raw_output = populate_list("RAW_OUTPUT=", line)

            # If everything is filled, we can stop
            if (filter_input and filter_forward
                    and filter_output and raw_output):
                break

        return {
            "FILTER_INPUT": filter_input,
            "FILTER_FORWARD": filter_forward,
            "FILTER_OUTPUT": filter_output,
            "RAW_OUTPUT": raw_output
        }

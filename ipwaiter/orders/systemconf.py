#!/usr/bin/env python3

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
            return SystemConfParser._grab_content_between_quotes(line.strip(token))
        else:
            return []

    def parse(self):
        filter_input = []
        filter_forward = []
        filter_output = []
        raw_output = []

        for line in self._read_conf():
            # If we are not filled yet, try this line
            if not filter_input:
                filter_input = SystemConfParser._attempt_populate_list("FILTER_INPUT=", line)

            # If we are not filled yet, try this line
            if not filter_forward:
                filter_forward = SystemConfParser._attempt_populate_list("FILTER_FORWARD=", line)

            # If we are not filled yet, try this line
            if not filter_output:
                filter_output = SystemConfParser._attempt_populate_list("FILTER_OUTPUT=", line)

            # If we are not filled yet, try this line
            if not raw_output:
                raw_output = SystemConfParser._attempt_populate_list("RAW_OUTPUT=", line)

            # If everything is filled, we can stop
            if filter_input and filter_forward and filter_output and raw_output:
                break

        return {
            "FILTER_INPUT": filter_input,
            "FILTER_FORWARD": filter_forward,
            "FILTER_OUTPUT": filter_output,
            "RAW_OUTPUT": raw_output
        }

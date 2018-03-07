#!/usr/bin/env python3

import sys


class Logger:

    def __init__(self):
        """Logger is purely a static implementation, no class instances"""
        raise NotImplementedError("No instances of Logger allowed")

    @staticmethod
    def log(message, *args):
        """Log a message to stdout"""
        if args:
            print("{}".format(message), args, file=sys.stdout)
        else:
            print("{}".format(message), file=sys.stdout)

    @staticmethod
    def e(message, *args):
        """Log an error message to stderr"""
        if args:
            print("ERROR  {}".format(message), args, file=sys.stderr)
        else:
            print("ERROR  {}".format(message), file=sys.stderr)

    @staticmethod
    def fatal(message, *args):
        """Log an error message to stderr and exit"""
        if args:
            print("FATAL  {}".format(message), args, file=sys.stderr)
        else:
            print("FATAL  {}".format(message), file=sys.stderr)
        sys.exit(1)

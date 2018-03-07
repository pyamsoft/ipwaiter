#!/usr/bin/env python3

import sh

from ..logger.logger import Logger


class Iptables:

    def __init__(self):
        self._cmd = sh.Command("iptables")

    def add(self, table, chain, args):
        if not table or not chain or not args:
            Logger.fatal("""Failed add() to iptables, missing argument
table: {}, chain: {}, args: {}""".format(table, chain, args))
        else:
            command = ["-t", table, "-A", chain]
            command += args
            result = self._cmd(
                command,
                _no_out=True,
                _no_err=True,
                _no_pipe=True
            )
            return result.exit_code == 0

    def link(self, table, parent_chain, target_chain):
        if not table or not parent_chain or not target_chain:
            Logger.fatal("""Failed link() to iptables, missing argument
table: {}, parent_chain: {}, target_chain: {}"""
                         .format(table, parent_chain, target_chain))
        else:
            result = self._cmd(
                "-t", table,
                "-A", parent_chain,
                "-j", target_chain
            )
            return result.exit_code == 0

    def create(self, table, chain):
        if not table or not chain:
            Logger.fatal("""Failed create() iptables, missing argument
table: {}, chain: {}""".format(table, chain))
        else:
            result = self._cmd(
                "-t", table,
                "-N", chain,
                _no_out=True,
                _no_err=True,
                _no_pipe=True
            )
            return result.exit_code == 0

    def flush(self, table, chain):
        if not table or not chain:
            Logger.fatal("""Failed flush() iptables, missing argument
table: {}, chain: {}""".format(table, chain))
        else:
            result = self._cmd(
                "-t", table,
                "-F", chain,
                _no_out=True,
                _no_err=True,
                _no_pipe=True
            )
            return result.exit_code == 0

    def unlink(self, table, parent_chain, target_chain):
        if not table or not parent_chain or not target_chain:
            Logger.fatal("""Failed unlink() from iptables, missing argument
table: {}, parent_chain: {}, target_chain: {}"""
                         .format(table, parent_chain, target_chain))
        else:
            result = self._cmd(
                "-t", table,
                "-D", parent_chain,
                "-j", target_chain,
                _no_out=True,
                _no_err=True,
                _no_pipe=True
            )
            return result.exit_code == 0

    def delete(self, table, chain):
        if not table or not chain:
            Logger.fatal("""Failed delete() from iptables, missing argument
table: {}, chain: {}""".format(table, chain))
        else:
            result = self._cmd(
                "-t", table,
                "-X", chain,
                _no_out=True,
                _no_err=True,
                _no_pipe=True
            )
            return result.exit_code == 0

    def exists(self, table, chain):
        if not table or not chain:
            Logger.fatal("""Failed exists() in iptables, missing argument
table: {}, chain: {}""".format(table, chain))
        else:
            try:
                result = self._cmd(
                    "-t", table,
                    "-L", chain,
                    _no_out=True,
                    _no_err=True,
                    _no_pipe=True
                )
                return result.exit_code == 0
            except sh.ErrorReturnCode:
                # We ignore the error here since this will fail if the
                # chain does not exist, and its too noisy
                return False

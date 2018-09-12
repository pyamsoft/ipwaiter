#!/usr/bin/env python3

import sh

from ..logger.logger import Logger


class Iptables:

    def __init__(self):
        self._cmd = sh.Command("iptables")

    def add(self, table, chain, args):
        if not table or not chain or not args:
            Logger.fatal(f"Failed add() to iptables, missing argument table: {table}, chain: {chain}, args: {args}")
        else:
            command = ["-t", table, "-A", chain]
            command += args
            return self._safe_command(*command)

    def link(self, table, parent_chain, target_chain):
        if not table or not parent_chain or not target_chain:
            Logger.fatal(
                f"Failed link() to iptables, missing argument table: {table}, parent_chain: {parent_chain}, "
                f"target_chain: {target_chain}")
        else:
            return self._safe_command(
                "-t", table,
                "-A", parent_chain,
                "-j", target_chain
            )

    def create(self, table, chain):
        if not table or not chain:
            Logger.fatal(f"Failed create() iptables, missing argument table: {table}, chain: {chain}")
        else:
            return self._safe_command("-t", table, "-N", chain)

    def flush(self, table, chain):
        if not table or not chain:
            Logger.fatal("Failed flush() iptables, missing argument table: {table}, chain: {chain}")
        else:
            return self._safe_command("-t", table, "-F", chain)

    def unlink(self, table, parent_chain, target_chain):
        if not table or not parent_chain or not target_chain:
            Logger.fatal(f"Failed unlink() from iptables, missing argument table: {table}, parent_chain: "
                         f"{parent_chain}, target_chain: {target_chain}")
        else:
            return self._safe_command(
                "-t", table,
                "-D", parent_chain,
                "-j", target_chain
            )

    def delete(self, table, chain):
        if not table or not chain:
            Logger.fatal(f"Failed delete() from iptables, missing argument table: {table}, chain: {chain}")
        else:
            return self._safe_command("-t", table, "-X", chain)

    def exists(self, table, chain):
        if not table or not chain:
            Logger.fatal(f"Failed exists() in iptables, missing argument table: {table}, chain: {chain}")
        else:
            return self._safe_command("-t", table, "-L", chain)

    def _safe_command(self, *args):
        try:
            result = self._cmd(args, _no_out=True, _no_err=True, _no_pipe=True)
            return result.exit_code == 0
        except sh.ErrorReturnCode:
            # We ignore the error here since this will fail if the
            # chain does not exist, and its too noisy
            return False

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

import subprocess

from ..logger.logger import Logger


class Iptables:

    def exists(self, table, chain):
        if not table or not chain:
            Logger.fatal(f"Failed exists() in iptables, arguments table: "
                         f"{table}, chain: {chain}")
        else:
            return self._safe_command("-t", table, "-L", chain)

    def create(self, table, chain):
        if not table or not chain:
            Logger.fatal(f"Failed create() iptables, arguments table: "
                         f"{table}, chain: {chain}")
        else:
            return self._safe_command("-t", table, "-N", chain)

    def flush(self, table, chain):
        if not table or not chain:
            Logger.fatal("Failed flush() iptables, arguments table: "
                         f"{table}, chain: {chain}")
        else:
            return self._safe_command("-t", table, "-F", chain)

    def delete(self, table, chain):
        if not table or not chain:
            Logger.fatal(f"Failed delete() from iptables, arguments "
                         f"table: {table}, chain: {chain}")
        else:
            return self._safe_command("-t", table, "-X", chain)

    # Rule operations

    def check_add(self, table, chain, args):
        if not table or not chain or not args:
            Logger.fatal(f"Failed check_add() on iptables, arguments "
                         f"table: {table}, chain: {chain}, args: {args}")
        else:
            command = ["-t", table, "-C", chain]
            command += args
            return self._safe_command(*command)

    def check_link(self, table, parent_chain, target_chain):
        if not table or not parent_chain or not target_chain:
            Logger.fatal(f"Failed check_unlink() from iptables, arguments "
                         f"table: {table}, parent_chain: "
                         f"{parent_chain}, target_chain: {target_chain}")
        else:
            return self._safe_command(
                "-t", table,
                "-C", parent_chain,
                "-j", target_chain
            )

    def add(self, table, chain, args):
        if not table or not chain or not args:
            Logger.fatal(f"Failed add() to iptables, arguments "
                         f"table: {table}, chain: {chain}, args: {args}")
        else:
            command = ["-t", table, "-A", chain]
            command += args
            return self._safe_command(*command)

    def link(self, table, parent_chain, target_chain):
        if not table or not parent_chain or not target_chain:
            Logger.fatal(
                f"Failed link() to iptables, arguments table: {table}, "
                f"parent_chain: {parent_chain}, "
                f"target_chain: {target_chain}")
        else:
            return self._safe_command(
                "-t", table,
                "-A", parent_chain,
                "-j", target_chain
            )

    def unlink(self, table, parent_chain, target_chain):
        if not table or not parent_chain or not target_chain:
            Logger.fatal(f"Failed unlink() from iptables, arguments "
                         f"table: {table}, parent_chain: "
                         f"{parent_chain}, target_chain: {target_chain}")
        else:
            return self._safe_command(
                "-t", table,
                "-D", parent_chain,
                "-j", target_chain
            )

    @staticmethod
    def _get_output():
        """Get output level based on debugging mode"""
        return None if Logger.enabled else subprocess.DEVNULL

    @staticmethod
    def _run(args):
        """Call subprocess command"""
        output = Iptables._get_output()
        if hasattr(subprocess, "run"):
            Logger.d("subprocess.run exists, using it")
            subprocess.run(
                args,
                check=True,
                stdin=output,
                stdout=output,
                stderr=output
            )
        else:
            Logger.d("subprocess.run does not exist, fallback to call")
            subprocess.check_call(
                args,
                stdin=output,
                stdout=output,
                stderr=output
            )

    @staticmethod
    def _safe_command(*args):
        try:
            Logger.d(f"Run iptables command: '{' '.join(args)}'")

            full_args = ["iptables"]
            for arg in args:
                full_args.append(arg)
            Iptables._run(full_args)
            return True
        except subprocess.CalledProcessError as e:
            # We ignore the error here since this will fail if the
            # chain does not exist, and its too noisy
            Logger.d("iptables command failed")
            Logger.d(e)
            return False

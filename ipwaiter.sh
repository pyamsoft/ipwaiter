#!/bin/sh

# The GPLv2 License
#
#   Copyright (C) 2017  Peter Kenji Yamanaka
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

__program="$(basename "$0")"
__version="0.0.4"
__system_dir="/etc/ipwaiter"
__system_conf="${__system_dir}/system.conf"
__orders_dir="${__system_dir}/orders"

error()
{
  if [ -n "$1" ]; then
    error_msg="$1"
    shift

    # shellcheck disable=SC2059
    printf -- "ERROR: ${error_msg}\\n" "$@"

    unset error_msg
  fi
}

print_usage()
{
  printf -- '
  %s [%s]

    General Commands
      add CHAIN ORDER
      remove CHAIN ORDER
      list

    System commands:
      hire
      rehire
      fire

    Available ORDER arguments are contained in "%s"

    Available CHAIN are:
      input   | INPUT
      forward | FORWARD
      output  | OUTPUT

    NOTE: If you specify your table with the advanced "raw" table
          then chain will be ignored and explicitly set to the raw
          table OUTPUT chain.
' "${__program}" "${__version}" "${__orders_dir}"
}

##
# Add order
# $1 - chain name
# $2 - order name
add_order()
{
  handle_order "$1" "$2" 1
}

##
# Delete order
# $1 - chain name
# $2 - order name
delete_order()
{
  handle_order "$1" "$2" 0
}

##
# If the input_orders, forward_orders, or output_orders chains do not exist, make them
create_chains_if_needed()
{
  if ! iptables -L input_orders > /dev/null 2>&1; then
    iptables -N input_orders || return 1
  fi

  if ! iptables -L forward_orders > /dev/null 2>&1; then
    iptables -N forward_orders || return 1
  fi

  if ! iptables -L output_orders > /dev/null 2>&1; then
    iptables -N output_orders || return 1
  fi

  return 0
}

##
# Check the chain name is valid
# $1 - Chain name
check_chain()
{
  case "$1" in
    INPUT)
      return 0
      ;;
    FORWARD)
      return 0
      ;;
    OUTPUT)
      return 0
      ;;
    *)
      error "Invalid chain name: %s" "$1"
      return 1
      ;;
  esac
}

##
# Load or delete orders in the iptables
# $1 - chain type, INPUT, FORWARD, OUTPUT
# $2 - order name
# $3 - 1 ADD, 0 DELETE
handle_order()
{
  handle_order__chain="$1"
  handle_order__name="$2"
  handle_order__arg="$3"

  for order_file in "${__orders_dir}"/*; do
    if [ "${handle_order__name}.order" = "$(basename "${order_file}")" ]; then
      # Found order, load
      create_chains_if_needed || return 1

      # Add
      if [ "${handle_order__arg}" -eq 1 ]; then
        # Only make the order if it does not already exist
        if ! iptables -L "order_${handle_order__name}" > /dev/null 2>&1; then
          printf -- 'ipwaiter is placing order: %s\n' "${handle_order__name}"
          # Create the chain
          iptables -N "order_${handle_order__name}" || return 1

          # Populate order chain with orders
          grep -v '^ *#' < "${order_file}" | while IFS= read -r order_line; do
            # Trim any leading or trailing spaces from the order
            order_line="$(printf -- '%s' "${order_line}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
            if [ -n "${order_line}" ]; then
              order_table="$(printf -- '%s' "${order_line}" | awk '{print $1}')"

              order_with_chain=1
              case "${order_table}" in
                raw)
                  order_with_chain=0
                  ;;
                filter)
                  order_with_chain=1
                  ;;
                *)
                  error "Unsupported table name: %s" "${order_table}"
                  return 1
              esac

              order_command="${order_line#${order_table}}"
              if [ "${order_with_chain}" -eq 1 ]; then
                # Place order on specific chain
                eval "iptables -t ${order_table} -A order_${handle_order__name} ${order_command}" > /dev/null || return 1
              else
                # Place order on OUTPUT chain with commend
                eval "iptables -t ${order_table} -A OUTPUT -m comment --comment 'ipwaiter: ${handle_order__name}' ${order_command}" > /dev/null || return 1
              fi

              unset order_table
              unset order_command
              unset order_line
            fi
          done

          # Add order chain to specified chain
          case "${handle_order__chain}" in
            INPUT)
              handle_order__chain="input_orders"
              ;;
            FORWARD)
              handle_order__chain="forward_orders"
              ;;
            OUTPUT)
              handle_order__chain="output_orders"
              ;;
            *)
              error "Invalid chain name: %s" "$1"
              return 1
              ;;
          esac
          iptables -A "${handle_order__chain}" -j "order_${handle_order__name}" || return 1

          printf -- 'ipwaiter has ordered: %s\n' "${handle_order__name}"
        fi
      else
        # Delete order only if they exist
        if  iptables -L "order_${handle_order__name}" > /dev/null 2>&1; then
          printf -- 'ipwaiter is returning order: %s\n' "${handle_order__name}"
          # Flush the orders first
          iptables -F "order_${handle_order__name}" || return 1

          # Delete order chain from specified chain
          case "${handle_order__chain}" in
            INPUT)
              handle_order__chain="input_orders"
              ;;
            FORWARD)
              handle_order__chain="forward_orders"
              ;;
            OUTPUT)
              handle_order__chain="output_orders"
              ;;
            *)
              error "Invalid chain name: %s" "$1"
              return 1
              ;;
          esac
          iptables -D "${handle_order__chain}" -j "order_${handle_order__name}" || return 1

          # Delete the chain
          iptables -X "order_${handle_order__name}" || return 1

          printf -- 'ipwaiter returned order: %s\n' "${handle_order__name}"
        fi
      fi

      unset handle_order__name
      unset handle_order__chain
      unset handle_order__args
      return 0
    fi
  done

  error "Could not find order matching %s in %s" "${handle_order__name}" "${__orders_dir}"
  unset handle_order__name
  return 1
}

##
# Lists the orders
list_orders() {
  for order_file in "${__orders_dir}"/*; do
    printf -- 'Order: %s\n' "$(basename "${order_file}")"
    printf -- '------\n'
    cat "${order_file}" || return 1
    printf -- '------\n\n'
  done
}

##
# Completely clears all orders off the table
fire_waiter()
{
  printf -- 'Firing old ipwaiter\n'

  for order_file in "${__orders_dir}"/*; do
    order_file="$(basename "${order_file}")"
    order="$(basename "${order_file}" '.order')"

    # Make sure we've actually found an order
    if [ "${order}" != "${order_file}" ]; then
      # Delete the orders from all chains we can find
      # If it fails, we don't care
      delete_order "INPUT" "${order}"
      delete_order "FORWARD" "${order}"
      delete_order "OUTPUT" "${order}"
    fi
  done

  # Delete the order chains
  iptables -F input_orders > /dev/null 2>&1
  iptables -X input_orders > /dev/null 2>&1

  iptables -F forward_orders > /dev/null 2>&1
  iptables -X forward_orders > /dev/null 2>&1

  iptables -F output_orders > /dev/null 2>&1
  iptables -X output_orders > /dev/null 2>&1

  printf -- 'Fired ipwaiter\n'
  return 0
}

##
# Load from the system config file
hire_waiter()
{
  printf -- 'Hiring new ipwaiter\n'

  # Prepare to source clean
  unset INPUT
  unset FORWARD
  unset OUTPUT

  if [ ! -e "${__system_conf}" ]; then
    error "Cannot load from system config, does not exist"
    return 1
  fi

  # Source system.conf
  # shellcheck disable=SC1090
  . "${__system_conf}"

  for order in ${INPUT}; do
    add_order "INPUT" "${order}"
  done

  for order in ${FORWARD}; do
    add_order "FORWARD" "${order}"
  done

  for order in ${OUTPUT}; do
    add_order "OUTPUT" "${order}"
  done

  printf -- 'Hired new ipwaiter\n'
  unset INPUT
  unset FORWARD
  unset OUTPUT
  return 0
}

main()
{
  if [ "$(id -u)" -ne 0 ]; then
    error "You must be root."
    print_usage
    return 1
  fi

  if [ -z "$1" ]; then
    error "Command needed"
    print_usage
    return 1
  fi

  case "$1" in
    add)
      shift

      # Case insensitive
      main__chain="$(printf -- '%s' "$1" | tr '[:lower:]' '[:upper:]')"
      if [ -z "${main__chain}" ]; then
        error "Must pass CHAIN to add command"
        print_usage
        return 1
      fi

      if [ -z "$2" ]; then
        error "Must pass ORDER to add command"
        print_usage
        return 1
      fi

      check_chain "${main__chain}" || return 1
      add_order "${main__chain}" "$2" || return 1
      unset main__chain
      ;;
    remove)
      shift

      # Case insensitive
      main__chain="$(printf -- '%s' "$1" | tr '[:lower:]' '[:upper:]')"
      if [ -z "${main__chain}" ]; then
        error "Must pass CHAIN to add command"
        print_usage
        return 1
      fi

      if [ -z "$2" ]; then
        error "Must pass ORDER to delete command"
        print_usage
        return 1
      fi

      check_chain "${main__chain}" || return 1
      delete_order "${main__chain}" "$2" || return 1
      unset main__chain
      ;;
    list)
      list_orders || return 1
      ;;
    hire)
      hire_waiter || return 1
      ;;
    fire)
      fire_waiter || return 1
      ;;
    rehire)
      fire_waiter || return 1
      hire_waiter || return 1
      ;;
    *)
      error "Invalid command %s" "$1"
      print_usage
      return 1
  esac
}

main "$@" || exit 1
exit 0
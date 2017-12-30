#!/bin/sh

installer()
{
  # Prepare directories
  mkdir -p /usr/bin
  mkdir -p /etc/ipwaiter/orders
  mkdir -p /etc/systemd/system

  # Install script
  install -m 755 -D ./ipwaiter /usr/bin || return 1

  # Install system config
  install -m 644 -D ./conf/system.conf /etc/ipwaiter || return 1

  # Install orders
  install -m 644 -D ./conf/orders/*.order /etc/ipwaiter/orders || return 1

  # Install systemd service
  install -m 644 -D ./conf/systemd/ipwaiter.service /etc/systemd/system || return 1
}

uninstaller()
{
  # Remove script
  rm -f /usr/bin/ipwaiter

  # Remove configuration directory
  rm -r -f /etc/ipwaiter

  # Stop the service
  systemctl disable ipwaiter.service

  # Remove the service
  rm -f /etc/systemd/system/ipwaiter.service
}

if [ "$(id -u)" -ne 0 ]; then
  echo "You must be root"
  exit 1
fi

if [ ! -e ./ipwaiter ]; then
  echo "Must run from ipwaiter root directory"
  exit 1
fi

if [ "$1" = "uninstall" ]; then
  uninstaller || exit 1
else
  installer || exit 1
fi

exit 0

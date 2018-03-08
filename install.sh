#!/bin/sh

DESTDIR="${DESTDIR:-/}"

installer()
{
  printf -- 'Installing...\n'

  # Prepare directories
  mkdir -p "${DESTDIR}/etc/ipwaiter/orders" || return 1
  mkdir -p "${DESTDIR}/usr/lib/systemd/system" || return 1

  # Install using python
  python setup.py install --root="${DESTDIR}" --optimize=1 || return 1

  # Install system config
  install -m 644 -D conf/system.conf "${DESTDIR}/etc/ipwaiter" || return 1

  # Install orders
  install -m 644 -D conf/orders/*.order "${DESTDIR}/etc/ipwaiter/orders" || return 1

  # Install systemd service
  install -m 644 -D conf/systemd/ipwaiter.service "${DESTDIR}/usr/lib/systemd/system" || return 1
}

uninstaller()
{
  printf -- 'Uninstalling...\n'

  pip uninstall ipwaiter || return 1

  # Remove configuration directory
  rm -r -f "${DESTDIR}/etc/ipwaiter" || return 1

  # Remove the service
  rm -f "${DESTDIR}/usr/lib/systemd/system/ipwaiter.service" || return 1
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

#!/bin/sh

DESTDIR="${DESTDIR:-/}"

installer()
{
  printf -- 'Installing...\n'

  # Set umask to permissive
  umask 022

  # Prepare directories
  mkdir -p "${DESTDIR}/etc/ipwaiter/install" || return 1
  mkdir -p "${DESTDIR}/etc/ipwaiter/orders" || return 1
  mkdir -p "${DESTDIR}/usr/lib/systemd/system" || return 1

  # Install using python
  python3 setup.py install \
    --record="${DESTDIR}/etc/ipwaiter/install/files.txt" \
    --root="${DESTDIR}" \
    --optimize=1 || return 1

  # Install system config
  install -m 644 -D conf/system.conf "${DESTDIR}/etc/ipwaiter" || return 1

  # Install orders
  install -m 644 -D conf/orders/*.order "${DESTDIR}/etc/ipwaiter/orders" || return 1

  # Install systemd service
  install -m 644 -D conf/systemd/ipwaiter.service "${DESTDIR}/usr/lib/systemd/system" || return 1

  # Install documentation
  install -m 644 -D README.md "${DESTDIR}/usr/share/doc/ipwaiter" || return 1

  # Install license
  install -m 644 -D LICENSE "${DESTDIR}/usr/share/licenses/ipwaiter" || return 1

  # Install bash completion
  install -m 644 -D res/shell/bash/bash_completion "${DESTDIR}/usr/share/bash-completion/completions/ipwaiter" || return 1
}

uninstaller()
{
  printf -- 'Uninstalling...\n'

  # Set umask to permissive
  umask 022

  # If pip knows about the package, it can uninstall it.
  if pip3 show ipwaiter > /dev/null; then
    pip3 uninstall -y ipwaiter || return 1
  else
    printf -- 'pip cannot find ipwaiter, installed to a non standard location?\n'
    install_history="${DESTDIR}/etc/ipwaiter/install/files.txt"
    if [ -e "${install_history}" ] && [ -r "${install_history}" ]; then
      # We can uninstall files manually
      while read -r file; do
        rm -f "${DESTDIR}/${file}" || return 1
      done < "${install_history}"
    else
      printf -- 'Cannot find list of installed files?\n'
      return 1
    fi
  fi

  # Remove configuration directory
  rm -r -f "${DESTDIR}/etc/ipwaiter" || return 1

  # Remove the service
  rm -f "${DESTDIR}/usr/lib/systemd/system/ipwaiter.service" || return 1

  # Remove license and directory
  rm -r -f "${DESTDIR}/usr/share/licenses/ipwaiter" || return 1

  # Remove docs
  rm -r -f "${DESTDIR}/usr/share/doc/ipwaiter" || return 1

  # Remove bash completion
  rm -f "${DESTDIR}/usr/share/bash-completion/completions/ipwaiter" || return 1
}

if [ "$(id -u)" -ne 0 ]; then
  echo "You must be root"
  exit 1
fi

if [ ! -e ./ipwaiter ]; then
  echo "Must run from ipwaiter root directory"
  exit 1
fi

if [ "$1" = "install" ]; then
  installer || exit 1
elif [ "$1" = "uninstall" ]; then
  uninstaller || exit 1
else
  printf -- '%s\n' "$(cat << EOF
  commands:
    install
    uninstall
EOF
)"
fi

exit 0

#!/usr/bin/env bash
# uninstalls abmatt
if [[ $EUID -ne 0 ]]; then
  echo 'Insufficient priveleges, must be root.'
  exit 1
fi

path=/usr/local
rm "${path}"/bin/abmatt && rm -rf "${path}"/etc/abmatt && echo '...abmatt has been removed.'
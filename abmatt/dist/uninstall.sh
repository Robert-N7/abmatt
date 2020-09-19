#!/usr/bin/env bash
# uninstalls abmatt
if [[ $EUID -ne 0 ]]; then
  echo 'Insufficient priveleges, must be root.'
  exit 1
fi

path=/usr/local
rm "${path}"/bin/abmatt
# rm "${path}"/bin/python*
rm "${path}"/
rm -rf "${path}"/etc/abmatt
rm -rf "${path}"/lib/abmatt
echo '...abmatt has been removed.'
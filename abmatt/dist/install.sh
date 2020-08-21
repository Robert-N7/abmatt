#!/usr/bin/env bash
# Installs abmatt, call with sudo ./install.sh

if [[ $EUID -ne 0 ]]; then
  echo 'Insufficient priveleges, must be root.'
  exit 1
fi

path="/usr/local"
bin_path="$path/bin/"
# Binaries
echo installing abmatt to "${bin_path}"
install -p bin/abmatt "$bin_path/abmatt"

# Other
etc_path="$path/etc/abmatt/"
mkdir -p "${etc_path}"
for file in etc/abmatt/*;do
  install -p "${file}" "${etc_path}"
echo '...done'

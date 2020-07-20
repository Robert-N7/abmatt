#!/usr/bin/env bash
# Installs abmatt, call with sudo ./install.sh

if [[ $EUID -ne 0 ]]; then
  echo 'Insufficient priveleges, must be root.'
  exit 1
fi

path="/usr/local"
etc_path="$path/etc/abmatt"
# Binaries
echo installing abmatt to "${path}"/bin
install -p bin/abmatt "${path}"/bin/abmatt

# Other
mkdir -p "${etc_path}"
install -p etc/abmatt/presets.txt "${etc_path}"/presets.txt
install -p etc/abmatt/config.conf "${etc_path}"/config.conf
echo '...done'

#!/usr/bin/env bash
# Installs abmatt, call with sudo ./install.sh

if [[ $EUID -ne 0 ]]; then
  echo 'Insufficient priveleges, must be root.'
  exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo 'export PATH="$DIR/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

#path="/usr/local"
#bin_path="$path/bin/"
## Binaries
#echo installing abmatt to "${bin_path}"
#mkdir -p "${bin_path}"
#for file in bin/abmatt/*;do
#  install -p "${file}" "${bin_path}"
#done
#
## Other
#etc_path="$path/etc/abmatt/"
#mkdir -p "${etc_path}"
#for file in etc/abmatt/*;do
#  install -p "${file}" "${etc_path}"
#done
#echo '...done'

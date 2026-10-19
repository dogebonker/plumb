#!/bin/sh
set -eu
case "${1:-}" in
 setup) python3 -m py_compile server.py ;;
 reset) : ;;
 start) exec python3 server.py ;;
 *) exit 2 ;;
esac

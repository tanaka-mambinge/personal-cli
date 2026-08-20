#!/bin/sh
set -eu

case "${1-}" in
  test)
    shift
    exec /opt/personal-cli/.venv/bin/pytest -v -o cache_dir=/tmp/pytest-cache "$@"
    ;;
  run)
    shift
    exec /opt/personal-cli/.venv/bin/python -m personal_cli "$@"
    ;;
  *)
    echo "Usage: personal-cli-docker {test|run} [arguments...]" >&2
    exit 2
    ;;
esac

#!/bin/bash

set -e

CACHE_DIR=data/cache

if [ -f $CACHE_DIR/shutuba.pkl ]; then
  mv $CACHE_DIR/shutuba.pkl $CACHE_DIR/shutuba.old.pkl
fi

if [[ -z $PYTHON_BIN ]]; then
  python task_notify_shutuba.py
else
  $PYTHON_BIN task_notify_shutuba.py
fi

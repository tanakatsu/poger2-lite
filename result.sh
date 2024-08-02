#!/bin/bash

set -e
CACHE_DIR=data/cache

if [ -f $CACHE_DIR/results.pkl ]; then
  mv $CACHE_DIR/results.pkl $CACHE_DIR/results.old.pkl
fi

if [[ -z $PYTHON_BIN ]]; then
  python task_notify_result.py
else
  $PYTHON_BIN task_notify_result.py
fi

#!/bin/bash

set -e

if [[ -z $PYTHON_BIN ]]; then
  python task_update_horse_names.py
  python task_update_horse_prizes.py
  python task_notify_ranking.py
else
  $PYTHON_BIN task_update_horse_names.py
  $PYTHON_BIN task_update_horse_prizes.py
  $PYTHON_BIN task_notify_ranking.py
fi

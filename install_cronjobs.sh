#!/bin/bash

if [ -f cronjobs.txt ]; then
  crontab -l > crontab_backup.txt 2>/dev/null
  (crontab -l 2>/dev/null; cat cronjobs.txt) | crontab -
  echo Install done.
else
  echo Before excuting this script, rename cronjobs.sample.txt to cronjobs.txt and edit it.
fi


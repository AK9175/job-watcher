#!/bin/zsh
export NTFY_TOPIC=notify-jobwatch-4a8512dc

cd "/Users/atharvakulkarni/Desktop/MS SE SJSU/Projects/Notify"
./.venv/bin/python main.py >> cron.log 2>&1

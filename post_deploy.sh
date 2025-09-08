#!/bin/bash
# Upgrade pip and force reinstall dependencies
python3 -m pip install --upgrade pip
python3 -m pip install --force-reinstall -r requirements.txt

# Start the bot
python3 bot.py

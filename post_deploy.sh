#!/bin/bash
# Force reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt

# Start bot
python bot.py

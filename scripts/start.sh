#!/bin/bash
service cron start
# nohup python3 discord-bot/bot.py &
gunicorn -w 2 -b 0.0.0.0:80 "starlink:create_app()"
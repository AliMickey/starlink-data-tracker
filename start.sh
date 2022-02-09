#!/bin/bash
service cron start
gunicorn -w 2 -b 0.0.0.0:80 "starlink:create_app()"
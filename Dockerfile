FROM python:3.11.5-slim

COPY . /app
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y sqlite3 cron python3 g++ && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt --no-cache-dir --verbose

COPY scripts/cronjobs /etc/cron.d/cronjobs
RUN crontab /etc/cron.d/cronjobs
RUN chmod 0600 /etc/cron.d/cronjobs
RUN chmod +x /app/scripts/backupDB.sh

EXPOSE 80

ENTRYPOINT ["sh","./scripts/start.sh"]
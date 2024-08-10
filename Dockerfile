FROM python:3.11.5-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       sqlite3 \
       cron \
       g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

COPY scripts/cronjobs /etc/cron.d/cronjobs
RUN crontab /etc/cron.d/cronjobs \
    && chmod 0600 /etc/cron.d/cronjobs

RUN chmod +x /app/scripts/backupDB.sh

EXPOSE 80

ENTRYPOINT ["sh", "./scripts/start.sh"]
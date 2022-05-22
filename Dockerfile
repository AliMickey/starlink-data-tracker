FROM python:slim

COPY . /app
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y sqlite3 cron python3 && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt --no-cache-dir

ADD scripts/cronjobs /etc/cron.d/cronjobs
RUN chmod 0600 /etc/cron.d/cronjobs

EXPOSE 80

ENTRYPOINT ["sh","./scripts/start.sh"]
FROM python:slim

COPY . /app
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y sqlite3 cron && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt --no-cache-dir

ADD backupDB /etc/cron.d/backupDB
RUN chmod 0600 /etc/cron.d/backupDB

EXPOSE 80

ENTRYPOINT ["sh","./start.sh"]
FROM python:slim

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 80

ENTRYPOINT ["sh","./gunicorn.sh"]
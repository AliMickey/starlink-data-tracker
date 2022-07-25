from flask import (current_app)

import smtplib
from threading import Thread
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText

# Create thread and pass variables
def sendEmail(recipient, header, message):
    password = current_app.config['MIGADU_KEY']
    thread = Thread(target=sendEmailThread, args=(recipient,header,message,password))
    thread.start()

# Send email to user
def sendEmailThread(recipient, header, message, password):
    msg = MIMEText(message, 'plain', 'utf-8')
    msg['Subject'] =  Header(header, 'utf-8')
    msg['From'] = formataddr((str(Header("Starlink Data Tracke", 'utf-8')), "admin@starlinktrack.com"))
    msg['To'] = recipient
    try:
        server = smtplib.SMTP_SSL('smtp.migadu.com', 465)
        server.login('admin@starlinktrack.com', password)
        server.sendmail("admin@starlinktrack.com", [recipient], msg.as_string() + "\n")
        server.quit()
    except Exception as e:
        print(f"Exception when sending email: {e}")
        pass
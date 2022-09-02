import schedule
from threading import Thread
from time import sleep

# Function to start schedule thread
def schedInitJobs():
    #schedule.every(10).minutes.do()
    thread = Thread(target=schedPendingRunner)
    thread.start()

# Function to keep scheduler running
def schedPendingRunner():
    while True:
        schedule.run_pending()
        sleep(60)
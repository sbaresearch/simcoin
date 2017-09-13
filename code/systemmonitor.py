import sched
import time
import logging


def run(stop_event, frequency):
    scheduler = sched.scheduler(time.time, time.sleep)
    next_execution = time.time()

    while not stop_event.wait(0):
        scheduler.enterabs(next_execution, 1, collect)
        next_execution += frequency
        scheduler.run()


def collect():
    logging.info('Do fancy stuff')
    time.sleep(.5)
    logging.info('Did fancy stuff')

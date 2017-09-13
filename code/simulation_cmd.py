from runner import Runner
import logging
import time
from postprocessing import PostProcessing
from event import Event
import config
import bash
from context import Context
from prepare import Prepare
from config import Path


def run():
    logging.info(config.log_line_run_start)

    path = Path()

    context = Context(path)
    context.create()

    runner = Runner(context)

    prepare = Prepare(context)
    runner.prepare = prepare

    post_processing = PostProcessing(context)
    runner.post_processing = post_processing

    event = Event(context)
    runner.event = event

    start = time.time()

    runner.run()

    logging.info("The duration of the simulation was {} seconds".format(str(time.time() - start)))

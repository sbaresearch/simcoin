from runner import Runner
import logging
import time
from postprocessing import PostProcessing
from event import Event
import config
from context import Context
from prepare import Prepare
from config import Path
from write import Writer


def run():
    context = Context()
    path = Path(context.run_name)
    context.path = path
    context.create()

    logging.info(config.log_line_run_start + context.run_name)

    writer = Writer(path.postprocessing_dir, context.args.tag)
    runner = Runner(context, writer)

    prepare = Prepare(context)
    runner.prepare = prepare

    postprocessing = PostProcessing(context, writer)
    runner.postprocessing = postprocessing

    event = Event(context)
    runner.event = event

    start = time.time()

    runner.run()

    logging.info("The duration of the run was {} seconds".format(str(time.time() - start)))

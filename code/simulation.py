from runner import Runner
import logging
import time
from postprocessing import PostProcessing
from event import Event
import config
import bash
from context import Context
from prepare import Prepare


def run():
    context = Context()
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

    logging.info("the duration of the experiment was {} seconds".format(str(time.time() - start)))
    bash.check_output('cp {} {}'.format(config.log_file, config.sim_dir))

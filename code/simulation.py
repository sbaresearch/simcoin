from runner import Runner
import logging
import time
from postprocessing import PostProcessing
from event import Event
import config
import bash
import utils


def run():
    args = utils.read_json_file(config.args_json)

    runner = Runner()

    post_processing = PostProcessing(runner)
    runner.post_processing = post_processing

    event = Event(runner, args.tick_duration)
    runner.event = event

    start = time.time()

    runner.run()

    logging.info("the duration of the experiment was {} seconds".format(str(time.time() - start)))
    bash.check_output('cp {} {}'.format(config.log_file, config.sim_dir))

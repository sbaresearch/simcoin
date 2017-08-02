from executor import Executor
import logging
import time
from postprocessing import PostProcessing
from event import Event
import utils
import argparse
import checkargs
import sys
import config
import bash


def parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('--tick-duration'
                        , default=1
                        , type=checkargs.check_positive_float
                        , help='Duration of ticks.')

    parser.add_argument('--verbose'
                        , default=False
                        , type=bool
                        , help='Verbose log.'
                        )

    args = parser.parse_known_args(sys.argv[2:])
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))
    return args


def run():
    args = parse()[0]

    utils.config_logger(args.verbose)

    executor = Executor()

    post_processing = PostProcessing(executor)
    executor.post_processing = post_processing

    event = Event(executor, args.tick_duration)
    executor.event = event

    start = time.time()

    executor.execute()

    logging.info("the duration of the experiment was {} seconds".format(str(time.time() - start)))
    bash.check_output('cp {} {}'.format(config.log_file, config.sim_dir))

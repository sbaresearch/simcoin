from runner import Runner
import logging
import time
from postprocessing import PostProcessing
from event import Event
import config
from context import Context
from prepare import Prepare
from write import Writer
import utils
import sys
import argparse
from simulationfiles import checkargs


def create_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--skip-ticks'
                        , type=checkargs.check_positive_int
                        , default=0
                        , help='Amount of ticks skipped for analysis at the beginning and at the end of the simulation'
                        )

    parser.add_argument('--tick-duration'
                        , default=1
                        , type=checkargs.check_positive_float
                        , help='Duration of ticks.')
    return parser


def run(unknown_arguments=False):
    for file in [config.ticks_csv, config.network_csv, config.nodes_csv]:
        utils.check_for_file(file)

    parser = create_parser()
    if unknown_arguments:
        args = parser.parse_known_args(sys.argv[2:])[0]
    else:
        args = parser.parse_args(sys.argv[2:])
    logging.info("Parsed arguments in {}: {}".format(__name__, args))
    utils.update_args(args)

    check_skip_ticks(args.skip_ticks)

    context = Context()
    context.create()

    logging.info(config.log_line_run_start + context.run_name)

    tag = context.args.tag
    if hasattr(context.args, 'tag_appendix'):
        tag += context.args.tag_appendix
    writer = Writer(tag)
    runner = Runner(context, writer)

    prepare = Prepare(context)
    runner._prepare = prepare

    postprocessing = PostProcessing(context, writer)
    runner._postprocessing = postprocessing

    event = Event(context)
    runner._event = event

    start = time.time()

    runner.run()

    logging.info("The duration of the run was {} seconds".format(str(time.time() - start)))


def check_skip_ticks(skip_ticks):
    amount_of_ticks = 0
    with open(config.ticks_csv, 'r') as file:
        for _ in file:
            amount_of_ticks += 1

    if amount_of_ticks <= 2 * skip_ticks:
        logging.error('You want to skip two times skip_ticks={} but you only have {} ticks in your {}.'
                      .format(skip_ticks, amount_of_ticks, config.ticks_csv_file_name))
        exit(-1)

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

    context = Context()
    context.create()

    logging.info(config.log_line_run_start + context.run_name)

    tag = context.args.tag
    if hasattr(context.args, 'tag_appendix'):
        tag += context.args.tag_appendix
    writer = Writer(tag)
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

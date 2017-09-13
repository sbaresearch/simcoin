import argparse
from simulationfiles import checkargs
import sys
import utils
import logging
import run_cmd


def create_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--repeat'
                        , default=2
                        , type=checkargs.check_positive_int
                        , help='Number of repetition of the simulation.'
                        )

    parser.add_argument('--tag'
                        , dest='tag'
                        , action="store"
                        , default='default_tag'
                        , help='A tag that will be added to every csv file.'
                        )

    return parser


def run():
    print('Called network config')

    parser = create_parser()
    args = parser.parse_known_args(sys.argv[2:])[0]

    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}\n".format(args))

    for i in range(args.repeat):
        logging.info('Starting {}/{} simulation'.format(i + 1, args.repeat))

        args.tag = args.tag + '-' + str(i)
        utils.update_args_json(args)

        run_cmd.run()
        logging.info('Finished {}/{} simulation'.format(i + 1, args.repeat))

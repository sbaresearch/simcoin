import argparse
from simulationfiles import checkargs
import sys
import utils
import logging
import run_cmd
import os
import config
import bash


files_to_concat = [
    config.blocks_csv_file_name,
    config.tips_csv_file_name,
    config.txs_csv_file_name,
    config.tx_exceptions_csv_file_name,
    config.block_exceptions_csv_file_name,
    config.rpc_exceptions_csv_file_name,
    config.blocks_received_csv_file_name,
    config.txs_received_csv_file_name,
    config.tick_infos_csv_file_name,
]


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
    logging.info('Called network config')

    parser = create_parser()
    args = parser.parse_known_args(sys.argv[2:])[0]
    logging.info("Parsed arguments in {}: {}".format(__name__, args))

    prepare()

    for i in range(args.repeat):
        logging.info('Starting {}/{} simulation'.format(i + 1, args.repeat))

        args.tag = args.tag + '-' + str(i)
        utils.update_args_json(args)

        run_cmd.run()
        bash.check_output('cp -r {}/postprocessing {}/run-{}'
                          .format(config.soft_link_to_run_dir, config.multi_run_dir, i + 1))
        logging.info('Finished {}/{} simulation'.format(i + 1, args.repeat))

    concat_files()


def prepare():
    os.makedirs(config.multi_run_dir)

    if os.path.islink(config.soft_link_to_multi_run_dir):
        bash.check_output('unlink {}'.format(config.soft_link_to_multi_run_dir))
    bash.check_output('ln -s {} {}'.format(config.multi_run_dir, config.soft_link_to_multi_run_dir))


def concat_files():
    for file in files_to_concat:
        bash.check_output('head -n 1 {}/run-1/{} > {}/{}'
                          .format(config.multi_run_dir, file, config.multi_run_dir, file))
        bash.check_output('sed -s 1d {}/*/{} >> {}/{}'
                          .format(config.multi_run_dir, file, config.multi_run_dir, file))

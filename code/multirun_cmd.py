import argparse
from simulationfiles import checkargs
import sys
import utils
import logging
import run_cmd
import os
import config
import bash
from cmd import rcmd
import parse
import systemmonitor
import clistats

files_to_concat = [
    parse.BlockCreateEvent.file_name,
    parse.BlockReceivedEvent.file_name,
    parse.BlockReconstructEvent.file_name,
    parse.BlockExceptionEvent.file_name,

    parse.UpdateTipEvent,
    parse.PeerLogicValidationEvent,

    parse.TxEvent.file_name,
    parse.TxReceivedEvent.file_name,
    parse.TxExceptionEvent.file_name,

    parse.RPCExceptionEvent.file_name,
    parse.TickEvent.file_name,

    clistats.Tip.file_name,
    config.step_times_csv_file_name,
    config.consensus_chain_csv_file_name,

    systemmonitor.CpuTimeSnapshot.file_name,
    systemmonitor.MemorySnapshot.file_name,
]


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--repeat'
                        , default=2
                        , type=checkargs.check_positive_int
                        , help='Number of repetition of the simulation.'
                        )

    args = parser.parse_known_args(sys.argv[2:])[0]
    utils.update_args_json(args)
    return args


def run():
    args = parse_args()
    logging.info("Parsed arguments in {}: {}".format(__name__, args))

    prepare()

    for i in range(args.repeat):
        logging.info('Starting {}/{} simulation'.format(i + 1, args.repeat))

        run_cmd.run('_run_' + str(i + 1))
        bash.check_output('cp -r {}/postprocessing {}/run-{}'
                          .format(config.soft_link_to_run_dir, config.multi_run_dir, i + 1))
        logging.info('Finished {}/{} simulation'.format(i + 1, args.repeat))

    bash.check_output('cp {} {}/.'.format(config.args_json, config.soft_link_to_multi_run_dir))
    bash.check_output('cp {} {}/.'.format(config.ticks_csv, config.soft_link_to_multi_run_dir))
    concat_files()

    bash.check_output(rcmd.create_report(config.multi_run_dir, config.multi_report_file_name))
    logging.info('Created {} report in folder={}'.format(config.multi_report_file_name, config.multi_run_dir))


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

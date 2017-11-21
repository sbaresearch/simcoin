import argparse
from simulationfiles import checkargs
import sys
import utils
import logging
from simulationfiles import nodes_config
from simulationfiles import ticks_config
from simulationfiles import network_config
import simulation_cmd
import os
import config
import bash
from cmd import rcmd
import parse
import systemmonitor
import clistats
from argparse import Namespace

files_to_concat = [
    config.analysed_tick_infos_file_name,
    parse.BlockCreateEvent.file_name_after_R_preprocessing,
    parse.BlockStatsEvent.file_name_after_R_preprocessing,
    parse.BlockReceivedEvent.file_name_after_R_preprocessing,
    parse.BlockReconstructEvent.file_name_after_R_preprocessing,
    parse.BlockExceptionEvent.file_name,
    parse.UpdateTipEvent.file_name_after_R_preprocessing,
    parse.PeerLogicValidationEvent.file_name_after_R_preprocessing,
    config.consensus_chain_csv_file_name,

    parse.TxEvent.file_name_after_R_preprocessing,
    parse.TxReceivedEvent.file_name_after_R_preprocessing,
    parse.TxExceptionEvent.file_name,

    parse.RPCExceptionEvent.file_name,
    clistats.Tip.file_name,

    config.step_times_csv_file_name,
    parse.TickEvent.file_name,

    systemmonitor.CpuTimeSnapshot.file_name,
    systemmonitor.MemorySnapshot.file_name,
]


def _parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--repeat'
                        , default=2
                        , type=checkargs.check_positive_int
                        , help='Number of repetition of the simulation.'
                        )

    args = parser.parse_known_args(sys.argv[2:])[0]
    utils.update_args(args)
    return args


def run():
    args = _parse_args()
    logging.info("Parsed arguments in {}: {}".format(__name__, args))

    _prepare()

    nodes_config.create(unknown_arguments=True)
    ticks_config.create(unknown_arguments=True)
    network_config.create(unknown_arguments=True)

    for i in range(args.repeat):
        logging.info('Starting {}/{} simulation'.format(i + 1, args.repeat))

        utils.update_args(Namespace(tag_appendix='_' + str(i + 1)))
        simulation_cmd.run(unknown_arguments=True)

        bash.check_output('cp -r {}/postprocessing {}/run-{}'
                          .format(config.soft_link_to_run_dir, config.soft_link_to_multi_run_dir, i + 1))
        logging.info('Finished {}/{} simulation'.format(i + 1, args.repeat))

    for file in [config.args_csv, config.ticks_csv, config.analysed_ticks_csv,
                 config.general_infos_csv, config.nodes_csv, config.network_csv]:
        bash.check_output('cp {} {}/.'.format(file, config.soft_link_to_multi_run_dir))
    _concat_files()

    bash.check_output(rcmd.create_report(config.soft_link_to_multi_run_dir))
    logging.info('Created report in folder={}'.format(config.soft_link_to_multi_run_dir))


def _prepare():
    os.makedirs(config.multi_run_dir)

    if os.path.islink(config.soft_link_to_multi_run_dir):
        bash.check_output('unlink {}'.format(config.soft_link_to_multi_run_dir))
    bash.check_output('cd {}; ln -s {} {}'.format(config.data_dir, config.multi_run_dir_name, config.last_multi_run))


def _concat_files():
    for file in files_to_concat:
        bash.check_output('head -n 1 {}/run-1/{} > {}/{}'
                          .format(config.multi_run_dir, file, config.multi_run_dir, file))
        bash.check_output('sed -s 1d {}/*/{} >> {}/{}'
                          .format(config.multi_run_dir, file, config.multi_run_dir, file))

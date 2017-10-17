import csv
import random
import pandas
import numpy as np
import config
from simulationfiles import nodes_config
import argparse
from simulationfiles import checkargs
import sys
import utils
import logging

np.set_printoptions(precision=2, suppress=True)


def create_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--amount-of-ticks'
                        , default=60
                        , type=checkargs.check_positive_int
                        , help='Amount of ticks.')

    parser.add_argument('--blocks-per-tick'
                        , default=0.1
                        , type=checkargs.check_positive_float
                        , help='Blocks per tick.'
                        )

    parser.add_argument('--txs-per-tick'
                        , default=1
                        , type=checkargs.check_positive_int
                        , help='Txs per tick.'
                        )

    parser.add_argument('--seed'
                        , default=0
                        , type=checkargs.check_positive_int
                        , help='Set the seed.'
                        )

    parser.add_argument('--tick-duration'
                        , default=1
                        , type=checkargs.check_positive_float
                        , help='Duration of ticks.')
    return parser


def create(unknown_arguments=False):
    logging.info('Called ticks config')

    utils.check_for_file(config.nodes_csv)
    nodes = utils.read_csv(config.nodes_csv)

    parser = create_parser()
    if unknown_arguments:
        args = parser.parse_known_args(sys.argv[2:])[0]
    else:
        args = parser.parse_args(sys.argv[2:])
    logging.info("Parsed arguments in {}: {}".format(__name__, args))
    utils.update_args(args)

    random.seed(args.seed)
    np.random.seed(args.seed)

    block_events = create_block_events(nodes, args.amount_of_ticks, args.blocks_per_tick)

    ticks = create_ticks(nodes, block_events, args.txs_per_tick, args.amount_of_ticks)

    logging.info('Created {}:'.format(config.ticks_csv))
    print(pandas.DataFrame(ticks))

    with open(config.ticks_csv, "w") as file:
        writer = csv.writer(file)
        writer.writerows(ticks)
    logging.info('End ticks config')


def calc_expected_events(number_of_ticks, events_per_tick):
    # 3 times + 10 to have some buffer
    return int(number_of_ticks * events_per_tick * 3) + 10


def create_block_events(nodes, amount_of_ticks, blocks_per_tick):
    expected_blocks = calc_expected_events(amount_of_ticks, blocks_per_tick)
    block_events = {}
    for node in nodes:
        block_events[node.name] = create_block_series(node.share, blocks_per_tick, expected_blocks)
    return block_events


def create_block_series(share, blocks_per_tick, expected_blocks):
    random_event_ticks = np.random.exponential((1 / blocks_per_tick) * (1 / share), expected_blocks)
    block_events = np.cumsum(random_event_ticks)
    return block_events.tolist()


def create_ticks(nodes, block_events, txs_per_tick, amount_of_ticks):
    index_tx = 0
    ticks = [[] for _ in range(amount_of_ticks)]
    for index, tick in enumerate(ticks):
        for i in range(txs_per_tick):
            tick.append('tx ' + random.choice(nodes).name)
            index_tx += 1

        for node in block_events.keys():
            pop_count = 0
            while block_events[node][0] < index + 1:
                tick.append('block ' + node)
                block_events[node].pop(0)
                pop_count += 1
            if pop_count > 1:
                print('A tick contains multiple block events for one node. '
                      'Please change your input arguments')
    return ticks

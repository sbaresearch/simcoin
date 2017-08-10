import csv
import random
import pandas
import numpy as np
import config
from simulationfiles import nodes_config
import argparse
import checkargs
import sys

np.set_printoptions(precision=2, suppress=True)


def create_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--amount-of-ticks'
                        , default=60
                        , type=checkargs.check_positive_int
                        , help='Amount of ticks.')

    parser.add_argument('--ticks-per-block'
                        , default=10
                        , type=checkargs.check_positive_int
                        , help='Ticks per block.'
                        )

    parser.add_argument('--tx-per-tick'
                        , default=1
                        , type=checkargs.check_positive_int
                        , help='Tx per tick.'
                        )

    parser.add_argument('--seed'
                        , default=0
                        , type=checkargs.check_positive_int
                        , help='Set the seed.'
                        )
    return parser


def create(unknown_arguments=False):
    print('Called ticks config')
    nodes = nodes_config.read()

    parser = create_parser()
    if unknown_arguments:
        args = parser.parse_known_args(sys.argv[2:])[0]
    else:
        args = parser.parse_args(sys.argv[2:])
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}\n".format(args))

    random.seed(args.seed)
    np.random.seed(args.seed)

    block_events = create_block_events(nodes, args.amount_of_ticks, args.ticks_per_block)

    ticks = create_ticks(nodes, block_events, args.tx_per_tick, args.amount_of_ticks)

    print('Created {}:'.format(config.ticks_csv))
    print(pandas.DataFrame(ticks))

    with open(config.ticks_csv, "w") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(ticks)
    print('End ticks config\n\n')


def calc_expected_events(number_of_ticks, events_per_tick):
    # 3 times + 10 to have some buffer
    return int(int(number_of_ticks * (1.0 / events_per_tick)) * 3) + 10


def create_block_events(nodes, amount_of_ticks, ticks_per_block):
    expected_blocks = calc_expected_events(amount_of_ticks, ticks_per_block)
    block_events = {}
    for node in nodes:
        block_events[node.name] = create_block_series(node.share, ticks_per_block, expected_blocks)
    return block_events


def create_block_series(share, ticks_per_block, expected_blocks):
    random_event_ticks = np.random.exponential(ticks_per_block * (1 / share), expected_blocks)
    block_events = np.cumsum(random_event_ticks)
    return block_events.tolist()


def create_ticks(nodes, block_events, tx_per_tick, amount_of_ticks):
    index_tx = 0
    ticks = [[] for _ in range(amount_of_ticks)]
    for index, tick in enumerate(ticks):
        for i in range(tx_per_tick):
            tick.append('tx ' + random.choice(nodes).name)
            index_tx += 1

        for node in block_events.keys():
            pop_count = 0
            while block_events[node][0] < index + 1:
                tick.append('block ' + node)
                block_events[node].pop(0)
                pop_count += 1
            if pop_count > 1:
                raise Exception("Intervals per block is too low. Only one block per node per tick is allowed. "
                                "Raise the ticks_per_block or try a different seeed. ")

    return ticks

import csv
import random
import pandas
import numpy as np
import config
import nodesconfig
import argparse
import checkargs
import sys

np.set_printoptions(precision=2, suppress=True)


def parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('--amount-of-intervals'
                        , default=60
                        , type=checkargs.check_positive_int
                        , help='Amount of intervals.')

    parser.add_argument('--intervals-per-block'
                        , default=10
                        , type=checkargs.check_positive_int
                        , help='Intervals per block.'
                        )

    parser.add_argument('--tx-per-interval'
                        , default=1
                        , type=checkargs.check_positive_int
                        , help='Tx per interval.'
                        )

    parser.add_argument('--seed'
                        , default=0
                        , type=checkargs.check_positive_int
                        , help='Set the seed.'
                        )

    args = parser.parse_args()
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))
    return args


def create():
    nodes = nodesconfig.read()

    args = parse()

    random.seed(args.seed)
    np.random.seed(args.seed)

    block_events = create_block_events(nodes, args.amount_of_intervals, args.intervals_per_block)

    intervals = create_intervals(nodes, block_events, args.tx_per_interval, args.amount_of_intervals)

    print(pandas.DataFrame(intervals))

    with open(config.interval_csv, "w") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(intervals)


def calc_expected_events(number_of_intervals, events_per_interval):
    # 3 times to have some buffer
    return int(int(number_of_intervals * (1.0 / events_per_interval)) * 3)


def create_block_events(nodes, amount_of_intervals, intervals_per_block):
    expected_blocks = calc_expected_events(amount_of_intervals, intervals_per_block)
    block_events = {}
    for node in nodes:
        block_events[node.name] = create_block_series(node.share, intervals_per_block, expected_blocks)
    return block_events


def create_block_series(share, intervals_per_block, expected_blocks):
    random_event_intervals = np.random.exponential(intervals_per_block * (1 / share), expected_blocks)
    block_events = np.cumsum(random_event_intervals)
    return block_events.tolist()


def create_intervals(nodes, block_events, tx_per_interval, amount_of_intervals):
    index_tx = 0
    intervals = [[] for _ in range(amount_of_intervals)]
    for index, interval in enumerate(intervals):
        for i in range(tx_per_interval):
            interval.append('tx ' + random.choice(nodes).name)
            index_tx += 1

        for node in block_events.keys():
            pop_count = 0
            while block_events[node][0] < index + 1:
                interval.append('block ' + node)
                block_events[node].pop(0)
                pop_count += 1
            if pop_count > 1:
                raise Exception("Intervals per block is too low. Only one block per node per interval is allowed. "
                                "Raise the intervals_per_block or try a different seeed. ")

    return intervals

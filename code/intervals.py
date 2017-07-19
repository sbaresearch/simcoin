import argparse
import csv
import random
import pandas
import sys
import numpy as np
import config
import checkargs


class Node:
    def __init__(self, name):
        self.name = name
        self.processed = 0
        self.block_events = []


def main():
    random.seed(1)
    np.random.seed(1)
    np.set_printoptions(precision=2, suppress=True)

    args = parse()
    nodes = create_nodes(args)

    intervals = create_intervals(nodes, args.tx_per_interval, args.amount_of_intervals)

    print(pandas.DataFrame(intervals))

    with open(config.interval_csv, "w") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(intervals)


def parse():
    parser = argparse.ArgumentParser(description='Create a simple {} for Bitcoin Network Simulator.'.format(config.interval_csv))

    parser.add_argument('--nodes'
                        , default=4
                        , type=checkargs.check_positive_int
                        , help='Number of Bitcoin nodes which generate blocks and tx.'
                        )

    parser.add_argument('--selfish-nodes'
                        , default=1
                        , type=checkargs.check_positive_int
                        , help='Number of selfish Bitcoin nodes which generate blocks and tx.'
                        )

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

    args = parser.parse_args()
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))

    return args


def create_nodes_array(number_of_nodes, number_of_selfish_nodes):
    nodes = [config.node_name.format(str(i)) for i in range(number_of_nodes)]
    nodes.extend([config.selfish_node_name.format(str(i)) for i in range(number_of_selfish_nodes)])

    return nodes


def calc_expected_events(number_of_intervals, events_per_interval):
    # 3 times to have some buffer
    return int(int(number_of_intervals * (1.0 / events_per_interval)) * 3)


def create_nodes(args):
    nodes = [Node(node) for node in create_nodes_array(args.nodes, args.selfish_nodes)]
    expected_blocks = calc_expected_events(args.amount_of_intervals, args.intervals_per_block)

    sum_of_shares = 0
    for node in nodes:
        share = round(float(input('Share of computation power of {} [0, 1]: '.format(node.name))), 2)
        node.block_events = create_block_events(share, args.intervals_per_block, expected_blocks)
        sum_of_shares += share
    if sum_of_shares != 1:
        raise Exception('Sum of shares should be 1.')

    return nodes


def create_block_events(share, intervals_per_block, expected_blocks):
    random_event_intervals = np.random.exponential(intervals_per_block * (1 / share), expected_blocks)
    block_events = np.cumsum(random_event_intervals)
    return block_events


def create_intervals(nodes, tx_per_interval, amount_of_intervals):
    index_tx = 0
    intervals = [[] for _ in range(amount_of_intervals)]
    for index, interval in enumerate(intervals):
        for i in range(tx_per_interval):
            interval.append('tx ' + random.choice(nodes).name)
            index_tx += 1

        for node in nodes:
            processed = node.processed
            while node.block_events[node.processed] < index + 1:
                interval.append('block ' + node.name)
                node.processed += 1
            if node.processed - processed > 1:
                raise Exception("Block interval is too low. Only one block per node per interval is allowed.")

    return intervals


if __name__ == "__main__":
    main()

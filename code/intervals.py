import argparse
import csv
import random
import pandas
import sys
import numpy as np
import config
from collections import Counter
import checkargs


def main():
    random.seed(1)
    np.random.seed(1)
    np.set_printoptions(precision=2, suppress=True)

    args = parse()

    nodes = create_nodes_array(args.nodes, args.selfish_nodes)

    expected_blocks = calc_expected_events(args.amount_of_intervals, args.blocks_per_interval)

    scale = 0.1
    block_events = create_events(scale, args.blocks_per_interval, expected_blocks)

    intervals = create_intervals(block_events, args.tx_per_interval, args.amount_of_intervals, nodes)

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

    parser.add_argument('--blocks-per-interval'
                        , default=10
                        , type=checkargs.check_positive_float
                        , help='Blocks per interval.'
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


def create_events(scale, events_per_interval, number_of_events):
    random_event_intervals = [(i + (1-scale)) * events_per_interval for i in list(np.random.exponential(scale, number_of_events))]
    return np.cumsum(random_event_intervals)


def create_intervals(block_events, tx_per_interval, amount_of_intervals, nodes):
    index_block = 0
    index_tx = 0
    intervals = [[] for _ in range(amount_of_intervals)]
    for index, interval in enumerate(intervals):
        for i in range(tx_per_interval):
            interval.append('tx ' + random.choice(nodes))
            index_tx += 1

        chosen_nodes = []
        while block_events[index_block] < index + 1:
            node = random.choice(nodes)
            chosen_nodes.append(node)
            interval.append('block ' + node)
            index_block += 1

        check_if_only_block_per_node(chosen_nodes)
    return intervals


def check_if_only_block_per_node(nodes):
    most_common = Counter(nodes).most_common(1)
    if len(most_common) > 0 and most_common[0][1] > 1:
        raise Exception("Block interval is too low. Only one block per node per interval is allowed.")


if __name__ == "__main__":
    main()

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

    nodes = create_nodes(args.nodes, args.selfish_nodes)

    expected_blocks = calc_expected_events(args.amount_of_ticks, args.block_interval)
    expected_tx = calc_expected_events(args.amount_of_ticks, args.tx_interval)

    scale = 0.1
    block_events = create_events(scale, args.block_interval, expected_blocks)
    tx_events = create_events(scale, args.tx_interval, expected_tx)

    ticks = create_ticks(block_events, tx_events, args.amount_of_ticks, nodes)

    print(pandas.DataFrame(ticks))

    with open(config.tick_csv, "w") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(ticks)


def parse():
    parser = argparse.ArgumentParser(description='Create a simple tick.config for Bitcoin Network Simulator.')

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

    parser.add_argument('--amount-of-ticks'
                        , default=60
                        , type=checkargs.check_positive_int
                        , help='Amount of ticks.')

    parser.add_argument('--block-interval'
                        , default=10
                        , type=checkargs.check_positive_float
                        , help='Block interval in ticks.'
                        )

    parser.add_argument('--tx-interval'
                        , default=1
                        , type=checkargs.check_positive_float
                        , help='Tx interval in ticks.'
                        )

    args = parser.parse_args()
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))

    return args


def create_nodes(number_of_nodes, number_of_selfish_nodes):
    nodes = [config.node_name.format(str(i)) for i in range(number_of_nodes)]
    nodes.extend([config.selfish_node_name.format(str(i)) for i in range(number_of_selfish_nodes)])

    return nodes


def calc_expected_events(number_of_ticks, event_interval):
    # 3 times to have some buffer
    return int(int(number_of_ticks * (1.0 / event_interval)) * 3)


def create_events(scale, event_interval, number_of_events):
    random_event_intervals = [(i + (1-scale)) * event_interval for i in list(np.random.exponential(scale, number_of_events))]
    return np.cumsum(random_event_intervals)


def create_ticks(block_events, tx_events, amount_of_ticks, nodes):
    index_block = 0
    index_tx = 0
    ticks = [[] for _ in range(amount_of_ticks)]
    for index, tick in enumerate(ticks):
        chosen_nodes = []
        while block_events[index_block] < index + 1:
            node = random.choice(nodes)
            chosen_nodes.append(node)
            tick.append('block ' + node)
            index_block += 1

        check_if_only_block_per_node(chosen_nodes)

        while tx_events[index_tx] < index + 1:
            tick.append('tx ' + random.choice(nodes))
            index_tx += 1
    return ticks


def check_if_only_block_per_node(nodes):
    most_common = Counter(nodes).most_common(1)
    if len(most_common) > 0 and most_common[0][1] > 1:
        raise Exception("Block interval={} is too low. "
                        "Only one block per node per tick is allowed.".format(args.block_interval))


if __name__ == "__main__":
    main()

import argparse
import csv
import random
import pandas
import sys
import numpy as np
import config
from collections import Counter

random.seed(1)
np.random.seed(1)
np.set_printoptions(precision=2, suppress=True)


def check_positive_float(value):
    float_value = float(value)
    check_positive(float_value)
    return float_value


def check_positive_int(value):
    int_value = int(value)
    check_positive(int_value)
    return int_value


def check_positive(value):
    if value < 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive value" % value)
    return value


def check_if_only_block_per_node(nodes):
    most_common = Counter(nodes).most_common(1)
    if len(most_common) > 0 and most_common[0][1] > 1:
        raise Exception("Block interval={} is too low. "
                        "Only one block per node per tick is allowed.".format(args.block_interval))


parser = argparse.ArgumentParser(description='Create a simple tick.config for Bitcoin Network Simulator.')


parser.add_argument('--nodes'
                    , default=4
                    , type=check_positive_int
                    , help='Number of Bitcoin nodes which generate blocks and tx.'
                    )

parser.add_argument('--selfish-nodes'
                    , default=1
                    , type=check_positive_int
                    , help='Number of selfish Bitcoin nodes which generate blocks and tx.'
                    )

parser.add_argument('--amount-of-ticks'
                    , default=60
                    , type=check_positive_int
                    , help='Amount of ticks.')

parser.add_argument('--block-interval'
                    , default=10
                    , type=check_positive_float
                    , help='Block interval in ticks.'
                    )

parser.add_argument('--tx-interval'
                    , default=1
                    , type=check_positive_float
                    , help='Tx interval in ticks.'
                    )

args = parser.parse_args()

print("arguments called with: {}".format(sys.argv))
print("parsed arguments: {}".format(args))

all_nodes = [config.node_prefix + str(i) for i in range(args.nodes)]
all_nodes.extend([config.selfish_node_prefix + str(i) for i in range(args.selfish_nodes)])

# generate 20% extra to have enough intervals
expected_blocks = int(int(args.amount_of_ticks * (1.0 / args.block_interval)) * 1.2)
expected_tx = int(int(args.amount_of_ticks * (1.0 / args.tx_interval)) * 1.2)

scale = 0.1
random_block_intervals = [(i + (1-scale)) * args.block_interval for i in list(np.random.exponential(scale, expected_blocks))]
random_tx_intervals = [(i + (1-scale)) * args.tx_interval for i in list(np.random.exponential(scale, expected_tx))]
block_point_in_time = np.cumsum(random_block_intervals)
tx_point_in_time = np.cumsum(random_tx_intervals)

index_block = 0
index_tx = 0
ticks = [[] for i in range(args.amount_of_ticks)]
for index, tick in enumerate(ticks):
    chosen_nodes = []
    while block_point_in_time[index_block] < index + 1:
        node = random.choice(all_nodes)
        chosen_nodes.append(node)
        tick.append('block ' + node)
        index_block += 1

    check_if_only_block_per_node(chosen_nodes)

    while tx_point_in_time[index_tx] < index + 1:
        tick.append('tx ' + random.choice(all_nodes))
        index_tx += 1

print(pandas.DataFrame(ticks))

with open(config.tick_csv, "w") as file:
    writer = csv.writer(file, delimiter=';')
    writer.writerows(ticks)

import csv
import random
import pandas
import numpy as np
import config
import utils
import nodesconfig

np.set_printoptions(precision=2, suppress=True)


def create():
    nodes = nodesconfig.read()

    amount_of_intervals = utils.get_non_negative_int('How many intervals do you want create?\n> ')

    intervals_per_block = utils.get_non_negative_int('How many intervals should pass by per block?\n> ')

    tx_per_interval = utils.get_non_negative_int('How many transactions per interval?\n> ')

    seed = utils.get_non_negative_int('Which seed do you want use?\n> ')

    random.seed(seed)
    np.random.seed(seed)

    block_events = create_block_events(nodes, amount_of_intervals, intervals_per_block)

    intervals = create_intervals(nodes, block_events, tx_per_interval, amount_of_intervals)

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
    return block_events


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

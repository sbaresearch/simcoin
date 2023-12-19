import csv
import random
import pandas
import config
import argparse
from simulationfiles import checkargs
import sys
import utils
import logging


def _create_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--seed'
                        , default=0
                        , type=checkargs.check_positive_int
                        , help='Set the seed'
                        )

    parser.add_argument('--connectivity'
                        , default=1
                        , type=checkargs.check_percentage
                        , help='Connectivity between nodes.'
                        )

    return parser


def create(unknown_arguments=False):
    logging.info('Called network config')

    utils.check_for_file(config.nodes_csv)
    nodes = utils.read_csv(config.nodes_csv)

    parser = _create_parser()
    if unknown_arguments:
        args = parser.parse_known_args(sys.argv[2:])[0]
    else:
        args = parser.parse_args(sys.argv[2:])
    logging.info("Parsed arguments in {}: {}".format(__name__, args))
    utils.update_args(args)

    random.seed(args.seed)

    header = _create_header(nodes)

    matrix = _create_matrix(header, args.connectivity)

    if _check_if_fully_connected(matrix) is not True:
        raise Exception("Not all nodes a reachable. Consider to raise the connectivity.")

    logging.info('Created {}:'.format(config.network_csv))
    print(pandas.DataFrame(matrix))

    with open(config.network_csv, "w") as file:
        writer = csv.writer(file)
        writer.writerows(matrix)
    logging.info('End network config')


def _create_header(nodes):
    header = ['']
    for node in nodes:
        name = node.name
        header.append(name)

    return header


def _create_matrix(header, connectivity):
    length = len(header)
    matrix = [[] for _ in range(length)]

    for i in range(1, length):
        matrix[i] = [-1 for _ in range(length)]
        matrix[i][0] = header[i]
    matrix[0] = header

    for i in range(1, length):
        for j in range(1, i + 1):
            if i is j:
                matrix[i][i] = 0
            elif random.random() < connectivity:
                if i % 2 == j % 2:
                    matrix[i][j] = 1
                    matrix[j][i] = 0
                else:
                    matrix[i][j] = 0
                    matrix[j][i] = 1
            else:
                matrix[i][j] = matrix[j][i] = 0
    return matrix


def _check_if_fully_connected(matrix):
    connected = _recursive_check(matrix)

    return len(connected) == len(matrix) - 1


def _recursive_check(matrix, visited=None, start=1):
    if visited is None:
        visited = {key: False for key in range(1, len(matrix))}

    if visited[start]:
        return []
    visited[start] = True
    output = [start]
    for neighbour in range(1, len(matrix)):
        if matrix[start][neighbour] > 0:
            output.extend(_recursive_check(matrix, visited, neighbour))
    return output


def read_connections():
    utils.check_for_file(config.network_csv)
    connections = {}
    with open(config.network_csv) as f:
        network_config = pandas.read_csv(f, index_col=0)
    
        for node_row, row in network_config.iterrows():
            connections[node_row] = []
            for node_column, value in row.iteritems():
                if node_column == node_row:
                    pass
                elif value == 1:
                    connections[node_row].append(node_column)

    return connections

import csv
import random
import pandas
import config
import nodesconfig
import argparse
import checkargs
import sys
import utils


def parse():
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

    args = parser.parse_known_args(sys.argv[2:])
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))
    return args


def create():
    args = parse()[0]

    nodes = nodesconfig.read()

    random.seed(args.seed)

    header = create_header(nodes)

    matrix = create_matrix(header, args.connectivity)

    if check_if_fully_connected(matrix) is not True:
        raise Exception("Not all nodes a reachable. Consider to raise the connectivity.")

    print(pandas.DataFrame(matrix))

    with open(config.network_csv, "w") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(matrix)


def create_header(nodes):
    header = ['']
    header.extend([node.name for node in nodes])

    return header


def create_matrix(header, connectivity):
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
                matrix[i][j] = matrix[j][i] = 1
            else:
                matrix[i][j] = matrix[j][i] = 0
    return matrix


def check_if_fully_connected(matrix):
    connected = recursive_check(matrix)

    return len(connected) == len(matrix) - 1


def recursive_check(matrix, visited=None, start=1):
    if visited is None:
        visited = {key: False for key in range(1, len(matrix))}

    if visited[start]:
        return []
    visited[start] = True
    output = [start]
    for neighbour in range(1, len(matrix)):
        if matrix[start][neighbour] > 0:
            output.extend(recursive_check(matrix, visited, neighbour))
    return output


def read_connections():
    utils.check_for_file(config.network_csv)
    connections = {}
    network_config = pandas.read_csv(open(config.network_csv), delimiter=';', index_col=0)

    for node_row, row in network_config.iterrows():
        if node_row.startswith(config.selfish_node_prefix):
            node_row += config.selfish_node_proxy_postfix
        connections[node_row] = []
        for node_column, value in row.iteritems():
            if node_column.startswith(config.selfish_node_prefix):
                node_column += config.selfish_node_proxy_postfix
            if node_column == node_row:
                pass
            elif value == 1:
                connections[node_row].append(node_column)

    return connections

import argparse
import csv
import random
import pandas
import sys
import config
import checkargs
import logging
import intervals


def main():
    random.seed(1)

    args = parse()

    nodes = args.nodes
    selfish_nodes = args.selfish_nodes

    header = create_header(nodes, selfish_nodes)
    matrix = create_matrix(header, args.latency, args.connectivity)

    if check_if_fully_connected(matrix) is not True:
        raise Exception("Not all nodes a reachable. Consider to raise the connectivity.")

    print(pandas.DataFrame(matrix))

    with open(config.network_config, "w") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(matrix)


def parse():
    parser = argparse.ArgumentParser(description='Create a simple network.config for Bitcoin Network Simulator.')

    parser.add_argument('--nodes'
                        , default=4
                        , type=checkargs.check_positive_int
                        , help='Number of Bitcoin nodes.'
                        )

    parser.add_argument('--selfish-nodes'
                        , default=1
                        , type=checkargs.check_positive_int
                        , help='Number of selfish Bitcoin nodes.'
                        )

    parser.add_argument('--latency'
                        , default=200
                        , type=checkargs.check_positive_int
                        , help='Latency of nodes in milliseconds.'
                        )

    parser.add_argument('--connectivity'
                        , default=.5
                        , type=checkargs.check_percentage
                        , help='Connectivity between nodes.'
                        )

    args = parser.parse_args()
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))

    return args


def create_header(nodes, selfish_nodes):
    header = ['']
    header.extend(intervals.create_nodes_array(nodes, selfish_nodes))

    return header


def create_matrix(header, latency, connectivity):
    length = len(header)
    matrix = [[] for _ in range(length)]

    for i in range(1, length):
        matrix[i] = [-1 for _ in range(length)]
        matrix[i][0] = header[i]
    matrix[0] = header

    for i in range(1, length):
        for j in range(1, i + 1):
            if i is j:
                matrix[i][i] = latency
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


def read_amount_of_nodes():
    nodes = selfish_nodes = 0
    network_config = pandas.read_csv(open(config.network_config), delimiter=';', index_col=0)

    for node_row, row in network_config.iterrows():
        if node_row.startswith(config.node_prefix):
            nodes += 1
        elif node_row.startswith(config.selfish_node_prefix):
            selfish_nodes += 1
        else:
            raise Exception('Unknown node type in {}'.format(config.network_config))
    logging.info('Parsed {} nodes and {} selfish nodes from {}'.format(nodes, selfish_nodes, config.network_config))
    return nodes, selfish_nodes


def read_connections():
    connections = {}
    network_config = pandas.read_csv(open(config.network_config), delimiter=';', index_col=0)

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


def read_latencies():
    latencies = {}
    network_config = pandas.read_csv(open(config.network_config), delimiter=';', index_col=0)

    for node_row, row in network_config.iterrows():
        if node_row.startswith(config.selfish_node_prefix):
            node_row += config.selfish_node_proxy_postfix
        for node_column, value in row.iteritems():
            if node_column.startswith(config.selfish_node_prefix):
                node_column += config.selfish_node_proxy_postfix
            if node_column == node_row:
                latencies[node_column] = value

    return latencies

if __name__ == "__main__":
    main()

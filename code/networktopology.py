import csv
import random
import pandas
import config
import nodesconfig
import utils


def create():
    nodes = nodesconfig.read()

    seed = utils.get_non_negative_int('Which seed do you want use for the networktopolgy?\n> ')

    connectivity = utils.get_percentage('What should be the connectivity?\n> ')

    random.seed(seed)

    header = create_header(nodes)

    matrix = create_matrix(header, connectivity)

    if check_if_fully_connected(matrix) is not True:
        raise Exception("Not all nodes a reachable. Consider to raise the connectivity.")

    print(pandas.DataFrame(matrix))

    with open(config.network_config, "w") as file:
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

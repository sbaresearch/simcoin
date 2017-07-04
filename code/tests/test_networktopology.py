from unittest import TestCase
import networktopology
from mock import patch
from mock import mock_open
from textwrap import dedent


class TestNetworktopology(TestCase):

    @patch('intervals.create_nodes_array')
    def test_create_header(self, mock):
        mock.return_value = ['node-0', 'selfish-node-1']

        header = networktopology.create_header(0, 0)

        self.assertEqual(len(header), 3)
        self.assertEqual(header[0], '')

    def test_create_matrix_full_connection(self):
        header = ['', 'node-0', 'node-1', 'node-2']
        latency = 200
        connectivity = 1

        matrix = networktopology.create_matrix(header, latency, connectivity)
        for i in range(1, len(header)):
            for j in range(1, len(header)):
                if i != j:
                    self.assertEqual(matrix[i][j], 1)

    def test_create_matrix_no_connection(self):
        header = ['', 'node-0', 'node-1', 'node-2']
        latency = 200
        connectivity = 0

        matrix = networktopology.create_matrix(header, latency, connectivity)
        for i in range(1, len(matrix)):
            for j in range(1, len(matrix)):
                if i != j:
                    self.assertEqual(matrix[i][j], 0)

    def test_create_matrix_latency(self):
        header = ['', 'node-0', 'node-1', 'node-2']
        latency = 200
        connectivity = 1

        matrix = networktopology.create_matrix(header, latency, connectivity)
        for i in range(1, len(header)):
            for j in range(1, len(header)):
                if i == j:
                    self.assertEqual(matrix[i][j], latency)

    DATA_1 = dedent("""
        ;node-0;node-1;selfish-node-0
        node-0;1;1;0
        node-1;1;2;1
        selfish-node-0;0;1;3
        """).strip()

    @patch("builtins.open", mock_open(read_data=DATA_1))
    def test_read_amount_of_nodes(self):
        nodes, selfish_nodes = networktopology.read_amount_of_nodes()

        self.assertEqual(nodes, 2)
        self.assertEqual(selfish_nodes, 1)

    DATA_2 = dedent("""
        ;some-node-0
        some-node-0;0
        """).strip()

    @patch("builtins.open", mock_open(read_data=DATA_2))
    def test_read_amount_of_nodes_unknown_node(self):
        with self.assertRaises(Exception) as context:
            networktopology.read_amount_of_nodes()

            self.assertEqual('Unknown node type in network.csv' in str(context))

    @patch("builtins.open", mock_open(read_data=DATA_1))
    def test_read_connections(self):
        connections = networktopology.read_connections()

        self.assertEqual(len(connections.keys()), 3)

        self.assertEqual(connections['node-0'], ['node-1'])
        self.assertEqual(connections['node-1'], ['node-0', 'selfish-node-0-proxy'])
        self.assertEqual(connections['selfish-node-0-proxy'], ['node-1'])

    @patch("builtins.open", mock_open(read_data=DATA_1))
    def test_read_latencies(self):
        latencies = networktopology.read_latencies()

        self.assertEqual(len(latencies.keys()), 3)

        self.assertEqual(latencies['node-0'], 1)
        self.assertEqual(latencies['node-1'], 2)
        self.assertEqual(latencies['selfish-node-0-proxy'], 3)

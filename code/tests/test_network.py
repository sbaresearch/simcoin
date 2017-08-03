from unittest import TestCase
import network
from mock import patch
from mock import mock_open
from textwrap import dedent
from nodesconfig import NodeConfig


class TestNetwork(TestCase):

    def test_create_header(self, ):
        header = network.create_header([NodeConfig('type', 'node-1', 0, 0), NodeConfig('type', 'node-2', 0, 0)])

        self.assertEqual(len(header), 3)
        self.assertEqual(header, ['', 'node-1', 'node-2'])

    def test_create_matrix_full_connection(self):
        header = ['', 'node-0', 'node-1', 'node-2']
        connectivity = 1

        matrix = network.create_matrix(header, connectivity)
        for i in range(1, len(header)):
            for j in range(1, len(header)):
                if i != j:
                    self.assertEqual(matrix[i][j], 1)

    def test_create_matrix_no_connection(self):
        header = ['', 'node-0', 'node-1', 'node-2']
        connectivity = 0

        matrix = network.create_matrix(header, connectivity)
        for i in range(1, len(matrix)):
            for j in range(1, len(matrix)):
                if i != j:
                    self.assertEqual(matrix[i][j], 0)

    DATA_1 = dedent("""
        ;node-0;node-1;selfish-node-0
        node-0;1;1;0
        node-1;1;2;1
        selfish-node-0;0;1;3
        """).strip()

    @patch("builtins.open", mock_open(read_data=DATA_1))
    @patch('utils.check_for_file', lambda file: None)
    def test_read_connections(self):
        connections = network.read_connections()

        self.assertEqual(len(connections.keys()), 3)

        self.assertEqual(connections['node-0'], ['node-1'])
        self.assertEqual(connections['node-1'], ['node-0', 'selfish-node-0-proxy'])
        self.assertEqual(connections['selfish-node-0-proxy'], ['node-1'])

    def test_check_if_fully_connected_1(self):
        matrix = [
            ['',        'node-0',   'node-1'],
            ['node-0',  1,          0],
            ['node-1',  0,          1]
        ]
        fully_connected = network.check_if_fully_connected(matrix)

        self.assertFalse(fully_connected)

    def test_check_if_fully_connected_2(self):
        matrix = [
            ['',        'node-0',   'node-1'],
            ['node-0',  1,          1],
            ['node-1',  1,          1]
        ]
        fully_connected = network.check_if_fully_connected(matrix)

        self.assertTrue(fully_connected)

    def test_check_if_fully_connected_3(self):
        matrix = [
            ['',        'node-0',   'node-1',   'node-2'],
            ['node-0',  1,          0,          1],
            ['node-1',  0,          1,          1],
            ['node-2',  1,          1,          1]
        ]
        fully_connected = network.check_if_fully_connected(matrix)

        self.assertTrue(fully_connected)

    def test_check_if_fully_connected_4(self):
        matrix = [
            ['',        'node-0',   'node-1',   'node-2'],
            ['node-0',  1,          0,          1],
            ['node-1',  0,          1,          0],
            ['node-2',  1,          0,          1]
        ]
        fully_connected = network.check_if_fully_connected(matrix)

        self.assertFalse(fully_connected)

    def test_check_if_fully_connected_5(self):
        matrix = [
            ['',        'node-0',   'node-1',   'node-2',   'node-3'],
            ['node-0',  1,          0,          0,          1],
            ['node-1',  0,          1,          1,          0],
            ['node-2',  0,          1,          1,          0],
            ['node-3',  1,          0,          0,          1],

        ]
        fully_connected = network.check_if_fully_connected(matrix)

        self.assertFalse(fully_connected)

    def test_check_if_fully_connected_6(self):
        matrix = [
            ['',        'node-0',   'node-1',   'node-2',   'node-3'],
            ['node-0',  1,          1,          0,          0],
            ['node-1',  1,          1,          1,          0],
            ['node-2',  0,          1,          1,          0],
            ['node-3',  0,          0,          0,          1],

        ]
        fully_connected = network.check_if_fully_connected(matrix)

        self.assertFalse(fully_connected)

from unittest import TestCase
from node import BitcoinNode
import config
from mock import MagicMock


class TestNode(TestCase):

    def setUp(self):
        self.node = BitcoinNode('node-1', 'ip', 'image')

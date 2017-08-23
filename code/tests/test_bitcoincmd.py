from unittest import TestCase
from cmd import bitcoincmd
from mock import MagicMock
import config


class TestBitcoincmd(TestCase):

    def test_start_selfish_mining(self):
        cmd = bitcoincmd.start_selfish_mining()

        self.assertTrue('  ' not in cmd)

    def test_start(self):
        node = MagicMock()
        cmd = bitcoincmd.start(node)

        self.assertTrue('  ' not in cmd)

    def test_rm_peers(self):
        cmd = bitcoincmd.rm_peers('node')

        self.assertTrue('  ' not in cmd)
        self.assertEqual(cmd, 'docker exec simcoin-node rm -f {}/regtest/peers.dat'.format(config.bitcoin_data_dir))

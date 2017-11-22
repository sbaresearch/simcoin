from unittest import TestCase
from cmd import bitcoincmd
from mock import MagicMock
import config


class TestBitcoincmd(TestCase):

    def test_start(self):
        cmd = bitcoincmd.start('node-1', '1.1.1.1', 'image', '/path', ['ip1', 'ip2'])

        self.assertTrue('  ' not in cmd)

    def test_rm_peers(self):
        cmd = bitcoincmd.rm_peers('node')

        self.assertTrue('  ' not in cmd)
        self.assertEqual(cmd, 'docker exec simcoin-node rm -f {}/regtest/peers.dat'.format(config.bitcoin_data_dir))

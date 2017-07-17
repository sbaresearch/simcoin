from unittest import TestCase
import bitcoincmd
from mock import MagicMock

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
        self.assertEqual(cmd, 'docker exec simcoin-node rm -f {}/regtest/peers.dat'.format(bitcoincmd.guest_dir))

    def test_get_best_block(self):
        cmd = bitcoincmd.get_best_block_hash('node')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('getbestblockhash' in cmd)

    def test_generate_block(self):
        cmd = bitcoincmd.generate_block('node', 2)

        self.assertTrue('  ' not in cmd)
        self.assertTrue('generate 2' in cmd)

    def test_generate_one_block(self):
        cmd = bitcoincmd.generate_block('node')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('generate 1' in cmd)

    def test_get_new_address(self):
        cmd = bitcoincmd.get_new_address('node')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('getnewaddress' in cmd)

    def test_send_to_address(self):
        cmd = bitcoincmd.send_to_address('node', 'address', 5)

        self.assertTrue('  ' not in cmd)
        self.assertTrue('sendtoaddress address 5' in cmd)

    def test_get_chain_tips(self):
        cmd = bitcoincmd.get_chain_tips('node')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('getchaintips' in cmd)

    def test_get_block_count(self):
        cmd = bitcoincmd.get_block_count('node')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('getblockcount' in cmd)

    def test_get_peer_info(self):
        cmd = bitcoincmd.get_peer_info('node')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('getpeerinfo' in cmd)

    def test_get_block_hash(self):
        cmd = bitcoincmd.get_block_hash('node', 5)

        self.assertTrue('  ' not in cmd)
        self.assertTrue('getblockhash 5' in cmd)

    def test_get_block(self):
        cmd = bitcoincmd.get_block('node', 'block_hash')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('getblock block_hash' in cmd)

    def test_connect(self):
        cmd = bitcoincmd.connect('node', 'ip1')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('addnode ip1 add')

    def text_exec_cli(self):
        cmd = bitcoincmd.exec_cli('node', 'cmd')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('bitcoin-cli -regtest -datadir={} cmd'.format(bitcoincmd.guest_dir) in cmd)

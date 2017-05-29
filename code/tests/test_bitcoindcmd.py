from unittest import TestCase
import bitcoindcmd
from plan import SelfishNode


class TestBitcoindcmd(TestCase):

    def test_start_selfish_miner_private_node(self):
        node = SelfishNode('name', '192.168.0.1', 'ip2s', 'args')
        cmd = bitcoindcmd.start_selfish_mining(node)

        print(cmd)
        self.assertTrue('-addnode=192.168.0.1' in cmd)
        self.assertTrue('  ' not in cmd)

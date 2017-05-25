from unittest import TestCase
import bitcoindcmd


class TestBitcoindcmd(TestCase):

    def test_start_selfish_miner_private_node(self):
        cmd = bitcoindcmd.start_selfish_mining('192.168.0.1')

        print(cmd)
        self.assertTrue('-addnode=192.168.0.1' in cmd)
        self.assertTrue('  ' not in cmd)

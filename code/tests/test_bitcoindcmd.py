from unittest import TestCase
import bitcoincmd


class TestBitcoindcmd(TestCase):

    def test_start_selfish_miner_private_node(self):
        cmd = bitcoincmd.start_selfish_mining()

        self.assertTrue('  ' not in cmd)

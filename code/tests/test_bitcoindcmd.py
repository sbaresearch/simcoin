from unittest import TestCase
import bitcoindcmd
from plan import SelfishNode


class TestBitcoindcmd(TestCase):

    def test_start_selfish_miner_private_node(self):
        cmd = bitcoindcmd.start_selfish_mining('ip')

        self.assertTrue('  ' not in cmd)

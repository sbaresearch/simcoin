from unittest import TestCase
from scheduler import Scheduler


class TestScheduler(TestCase):
    def test_add_blocks(self):
        s = Scheduler()
        s.addblocks(10, "echo Hello")

    def test_bash_commands(self):
        s = Scheduler()
        s.addblocks(10, ["echo Hello","generate block 1","generate block 2"])
        s.addtransactions(4, ["transact a -> b","transact b -> c ","transact c -> d"])
        x = s.bash_commands()

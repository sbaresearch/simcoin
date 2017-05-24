from unittest import TestCase
from scheduler import Scheduler


class TestScheduler(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestScheduler, self).__init__(*args, **kwargs)

        self.scheduler = Scheduler()

    def test_add_blocks(self):
        self.scheduler.add_blocks(10, 100, "echo Hello")

    def test_bash_commands(self):
        self.scheduler.add_blocks(10, 100, ["echo Hello", "generate block 1", "generate block 2"])
        self.scheduler.add_transactions(4, ["transact a -> b", "transact b -> c ", "transact c -> d"])
        self.scheduler.bash_commands()

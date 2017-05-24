from unittest import TestCase
from scheduler import Scheduler


class TestScheduler(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestScheduler, self).__init__(*args, **kwargs)

        self.scheduler = Scheduler(0)

    def test_add_blocks_one_block(self):
        self.scheduler.add_blocks(1, 100, ['cmd'])

        self.assertEqual(len(self.scheduler), 1)
        self.assertEqual(self.scheduler[0][0], 79.587450816311005)
        self.assertEqual(self.scheduler[0][1], 'cmd')

    def test_add_blocks_ten_blocks(self):
        self.scheduler.add_blocks(10, 1, ['cmd'])

        self.assertEqual(len(self.scheduler), 10)

        previous = (0, 'cmd')
        for cmd in self.scheduler:
            self.assertTrue(cmd[0] > previous[0])
            self.assertEqual(cmd[1], 'cmd')
            previous = cmd

    def test_add_tx_one_second(self):
        self.scheduler.add_tx(1, ['cmd'], 1)

        self.assertEqual(len(self.scheduler), 1)
        self.assertEqual(self.scheduler[0][0], 1.0)
        self.assertEqual(self.scheduler[0][1], 'cmd')

    def test_add_tx_ten_seconds(self):
        self.scheduler.add_tx(10, ['cmd'], 1)

        self.assertEqual(len(self.scheduler), 10)

        previous = (0, 'cmd')
        for cmd in self.scheduler:
            self.assertTrue(cmd[0] > previous[0])
            self.assertEqual(cmd[1], 'cmd')
            previous = cmd

    def test_add_tx_2_tx_per_second(self):
        self.scheduler.add_tx(10, ['cmd'], 2)

        self.assertEqual(len(self.scheduler), 20)

    def test_bash_commands(self):
        self.scheduler.add_blocks(10, 100, ["echo Hello", "generate block 1", "generate block 2"])
        self.scheduler.add_tx(4, ["transact a -> b", "transact b -> c ", "transact c -> d"])
        self.scheduler.bash_commands()

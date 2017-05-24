import numpy
import itertools
    #
    # scheduler.add(interval_in_seconds=10*60,distribution="poisson",cmd="generateblock 1 true")
    # scheduler.add("every ten 10 minutes on average Poisson distributed trigger block found")
    # scheduler.add("every 30 minutes add 1 % of nodes")
    # scheduler.add("every `1/2.5` seconds create transaction")
    # scheduler.onFinish(lambda: print("hello world"))
    # schedule = scheduler.getSchedule()


class Scheduler(list):

    def __init__(self, seed):
        list.__init__(self)
        self.seed = seed

    def append(self, item):
        self.append(item)

    def merge(self, delay_queue):
        self.extend(delay_queue)
        self.sort()

    def add_blocks(self, count, block_interval, cmd):
        numpy.random.seed(self.seed)
        random_numbers = numpy.random.exponential(scale=block_interval, size=count)
        points_in_time = itertools.accumulate(random_numbers)
        cmds = itertools.cycle(cmd)
        cmds_with_point_in_time = zip(points_in_time, cmds)
        self.merge(cmds_with_point_in_time)

    def add_transactions(self, until, cmd, transactions_per_second=1):
        tx_interval = 1.0 / transactions_per_second
        points_in_time = numpy.arange(tx_interval, until + tx_interval, tx_interval)
        cmds = itertools.cycle(cmd)
        cmds_with_time = zip(points_in_time, cmds)
        self.merge(cmds_with_time)

    def bash_commands(self):
        times, cmds = zip(*self)
        prev_times = [0] + list(times)
        time_tuples = list(zip(prev_times, times))
        deltas = list(map(lambda x: x[1]-x[0], time_tuples))
        sleeps = list(map((lambda t: " sleep {:5.5f} ; {} \n".format(t[0], t[1])), zip(deltas, cmds)))
        plan = "echo Begin of Scheduled commands\n {}".format(" ".join(sleeps))
        return plan

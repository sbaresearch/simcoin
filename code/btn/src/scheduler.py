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

    def __init__(self):
        list.__init__(self)

    def append(self, item):
        self.append(item)

    def merge(self, delay_queue):
        self.extend(delay_queue)
        self.sort()

    def addblocks(self,count, blockTime, cmd):
        numpy.random.seed(0)
        s = numpy.random.exponential(scale=blockTime, size=count, ) # TODO set to 600
        ss = itertools.accumulate(s)
        f = itertools.cycle( cmd )
        fs = zip(ss,f)
        self.merge(fs)

    def addtransactions(self, count, cmd, transactionsPerSecond = 1):
        tps = 1  # transactions per second TODO set to 2.5
        time = numpy.arange(1.0, count,1.0/transactionsPerSecond)
        # times = itertools.accumulate(time)
        f = itertools.cycle(cmd)
        plan = zip(time, f)
        self.merge(plan)

    def bash_commands(self):
        times, cmds = zip(*self)
        prev_times = [0] + list(times)
        time_tuples = list(zip(prev_times, times))
        deltas = list(map(lambda x: x[1]-x[0], time_tuples))
        sleeps = list(map((lambda t : " sleep {:5.5f} ; {} \n".format(t[0],t[1])),zip(deltas,cmds)))
        plan = "echo Begin of Scheduled commands\n {}".format(" ".join(sleeps))
        return plan

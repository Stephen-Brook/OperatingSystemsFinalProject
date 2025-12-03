from abc import ABC, abstractmethod
import random
from process import Process, ProcessStatus

class Scheduler(ABC):
    name: str
    #if true, can preempt at each preemptive_tick, if false, each process must run to completion
    preemptive: bool = False
    #static time interval for preemptive schedulers
    preemptive_tick: int

    @abstractmethod
    def pick_next(self, ready, now, current):
        ...

    #allow a scheduler to dynamically choose the interrupt interval per dispatch
    #returing >= 1 means that the chosen process will run for that many ticks unless it finishes or blocks earlier
    #by default, a use preemptive_tick, else use 1
    def preempt_interval(self, now, current):
        return max(1, getattr(self, "preemptive_tick", 1))

# simple round robin scheduler
class RoundRobin(Scheduler):
    name = "rr"
    preemptive = True
    preemptive_tick = 4

    def __init__(self):
        self.queue = []

    def pick_next(self, ready, now, current):
        #update the queue to match the ready processes
        ready_names = set(p.name for p in ready)
        self.queue = [p for p in self.queue if p.name in ready_names]
        for p in ready:
            if p.name not in (q.name for q in self.queue):
                self.queue.append(p)

        if not self.queue:
            return None

        if current and current.status != ProcessStatus.TERMINATED:
            #if the current process is still running, keep it at the front of the queue
            return current

        #get the next process in the queue
        next_process = self.queue.pop(0)
        self.queue.append(next_process)
        return next_process

# pick the process with the highest priority at each scheduling decision
class PriorityPreemptive(Scheduler):
    name = "pripreempt"
    preemptive = True
    preemptive_tick = 1

    def pick_next(self, ready, now, current):
        if not ready:
            return None
        #pick the process with the highest priority (lowest numeric value)
        return max(ready, key=lambda p: (p.priority, p.simulated_arrival_time, p.name))

# pick the process with the highest priority when the cpu is free
class PriorityNonPreemptive(Scheduler):
    name = "prinonpreempt"
    preemptive = False

    def pick_next(self, ready, now, current):
        if current and current.status != ProcessStatus.TERMINATED:
            #non preemptive, keep running the current process at each interrupt
            return current
        if not ready:
            return None
        #if the current process is done, get the process with the highest priority (lowest numeric value)
        return max(ready, key=lambda p: (p.priority, p.simulated_arrival_time, p.name))

# pick the process that arrived first when the cpu is free
class FirstComeFirstServe(Scheduler):
    name = "fcfs"
    preemptive = False

    def pick_next(self, ready, now, current):
        if current and current.status != ProcessStatus.TERMINATED:
            #non preemptive, keep running the current process at each interrupt
            return current
        if not ready:
            return None
        #if the current process is done, get the process with the earliest arrival time
        return min(ready, key=lambda p: (p.simulated_arrival_time, p.name))

# pick the process with the highest response ratio (waiting/service_time) when the cpu is free
class HighestResponseRatioNext(Scheduler):
    name = "hrrn"
    preemptive = False

    def pick_next(self, ready, now, current):
        if current and current.status != ProcessStatus.TERMINATED:
            #non preemptive, keep running the current process at each interrupt
            return current

        def response_ratio(p):
            waiting_time = now - p.arrival_tick
            return (waiting_time + p.service_time) / p.service_time

        return max(ready, key=response_ratio)

#pick the process with the least remaining time at each scheduling decision
class ShortestRemainingTime(Scheduler):
    name = "srt"
    preemptive = True
    preemptive_tick = 1

    def pick_next(self, ready, now, current):
        if not ready:
            return None
        #pick the process with the shortest remaining time
        return min(ready, key=lambda p: (p.remaining_time, p.simulated_arrival_time, p.name))

#pick the process with the longest remaining time at each scheduling decision
class LongestRemainingTime(Scheduler):
    name = "lrt"
    preemptive = True
    preemptive_tick = 1

    def pick_next(self, ready, now, current):
        if not ready:
            return None
        #pick the process with the longest remaining time
        return max(ready, key=lambda p: (p.remaining_time, p.simulated_arrival_time, p.name))

#pick the process with the least remaining time when the cpu is free
class ShortestJobNext(Scheduler):
    name = "sjn"
    preemptive = False

    def pick_next(self, ready, now, current):
        if current and current.status != ProcessStatus.TERMINATED:
            #non preemptive, keep running the current process at each interrupt
            return current
        if not ready:
            return None
        #if the current process is done, get the process with the shortest time required on the cpu
        return min(ready, key=lambda p: (p.service_time, p.simulated_arrival_time, p.name))

#pick the process with the most remaining time when the cpu is free
class LongestJobNext(Scheduler):
    name = "ljn"
    preemptive = False

    def pick_next(self, ready, now, current):
        if current and current.status != ProcessStatus.TERMINATED:
            #non preemptive, keep running the current process at each interrupt
            return current
        if not ready:
            return None
        #if the current process is done, get the process with the longest time required on the cpu
        return max(ready, key=lambda p: (p.service_time, p.simulated_arrival_time, p.name))

#give each process a number of tickets proportional to its priotity
#at each scheduling decision choose a ticket at random to pick the next process
class Lottery(Scheduler):
    name = "lottery"
    preemptive = True
    preemptive_tick = 3

    def tickets_for(self, p):
        return max(1, int(p.priority))

    def pick_next(self, ready, now, current):
        if not ready:
            return None
        pool = []
        for p in ready:
            pool.extend([p] * self.tickets_for(p))
        return random.choice(pool)
    
#processes that have waited longer get both higher selection priority and a longer slice
class DynamicAgingRR(Scheduler):
    name = "dyn_aging_rr"
    preemptive = True

    #minimum time slice for preemption
    base_quantum = 2
    #maximum time slice for preemption
    max_quantum = 8
    #how quickly age increases time slice
    age_boost_div = 3
    #how numeric priority influnces which process is selected next
    priority_weight: float = 1.2

    def __init__(self):
        self.last_dispatch_time = {}
        self.first_ready_seen_at = {}

    #age since either first becoming ready or last dispatched
    def _age(self, p, now):
        start = self.last_dispatch_time.get(p.name, self.first_ready_seen_at.get(p.name, now))
        return max(0, now - start)

    def pick_next(self, ready, now, current):
        if not ready:
            return None

        #initialize first-seen ready timestamps
        for p in ready:
            if p.name not in self.first_ready_seen_at:
                self.first_ready_seen_at[p.name] = now

        #score = age + (priority_weight * priority)
        def score(p):
            return self._age(p, now) + self.priority_weight * float(p.priority)

        chosen = max(ready, key=score)

        #mark the dispatch moment, we need this for age calculation
        self.last_dispatch_time[chosen.name] = now
        return chosen

    #start with base_quantum (2)
    #grow with the processes waiting age
    #don't exceed max_quantum (8)
    #don't exceed the processes remaining_time (no over allocation)
    def preempt_interval(self, now, current):
        if current is None:
            return max(1, getattr(self, "base_quantum", 2))

        age = self._age(current, now)
        grow = age // max(1, self.age_boost_div)
        q = self.base_quantum + grow
        q = min(q, int(max(1, current.remaining_time)))
        q = min(q, self.max_quantum)
        return max(1, q)


#add new algorithms here and register them:
REGISTRY = {
    Lottery.name: Lottery,
    DynamicAgingRR.name: DynamicAgingRR,
    RoundRobin.name: RoundRobin,
    FirstComeFirstServe.name: FirstComeFirstServe,
    ShortestRemainingTime.name: ShortestRemainingTime,
    ShortestJobNext.name: ShortestJobNext,
    LongestRemainingTime.name: LongestRemainingTime,
    LongestJobNext.name: LongestJobNext,
    HighestResponseRatioNext.name: HighestResponseRatioNext,
    PriorityPreemptive.name: PriorityPreemptive,
    PriorityNonPreemptive.name: PriorityNonPreemptive,
}
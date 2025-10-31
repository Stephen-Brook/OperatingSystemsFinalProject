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
        return min(ready, key=lambda p: (p.remaining_time, p.simulated_arrival_time, p.name))

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
    base_quantum: int = 2
    #maximum time slice for preemption
    max_quantum: int = 8
    #how quickly age increases time slice
    age_boost_div: int = 3
    #how numeric priority influnces which process is selected next
    priority_weight: float = 0.5

    def __init__(self):
        self.last_dispatch_time = {}
        self.first_ready_seen_at = {}

    #age since either first becoming ready or last dispatched
    def _age(self, p, now: int):
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
    ShortestJobNext.name: ShortestJobNext,
    Lottery.name: Lottery,
    DynamicAgingRR.name: DynamicAgingRR,
}
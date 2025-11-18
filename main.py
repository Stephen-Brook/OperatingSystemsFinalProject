import argparse
from process import Process, ProcessStatus
from schedulers import REGISTRY, Scheduler
import csv
import time

#create a set of processes
#n is the number of processes
def generate_processes(n):
    return [Process(f"Process-{i+1}") for i in range(n)]

#clone the list of processes so each scheduling algorithm has its own list
def clone_processes(template):
    clones = []
    for t in template:
        p = Process(t.name)
        p.priority = t.priority
        p.simulated_arrival_time = t.simulated_arrival_time
        p.service_time = t.service_time
        p.remaining_time = t.service_time
        return_to_defaults(p)
        clones.append(p)
    return clones

#set all the metrics that the algorithms will increment to their defaults
def return_to_defaults(p):
    p.status = ProcessStatus.NEW
    p.arrival_tick = None
    p.completion_tick = None
    p.turnaround_time = None
    p.waiting_time = None
    p.remaining_time = p.service_time

#see if there are any new processes to admit for some given time step
def admit_new_arrivals(processes, now):
    for p in processes:
        if p.status == ProcessStatus.NEW and p.simulated_arrival_time <= now:
            p.ready(now)

#get a list of all ready processes
def get_ready(processes):
    ready_processes = []
    for p in processes:
        if p.status == ProcessStatus.READY:
            ready_processes.append(p)
    return ready_processes

#check to see if all of the process are done
def all_done(processes):
    for p in processes:
        if p.status != ProcessStatus.TERMINATED:
            return False
    return True

#simulate 1 time step
#preemptive algorithms can preempt using their preemptive_tick value
def simulate(processes, scheduler):
    now = 0
    current = None

    #track how many ticks remain before preemptive schedulers can preempt processes
    slice_remaining = None

    #repeat until all processes are done
    while not all_done(processes):
        #admit new arrivals for the current time step
        admit_new_arrivals(processes, now)
        #get all of the ready processes
        ready = get_ready(processes)

        #if there are no ready processes, and there is no current process or the current process is done
        if not ready and (current is None or current.status == ProcessStatus.TERMINATED):
            #skip to either the next time step, or the arrival time of the next process
            future = [p.simulated_arrival_time for p in processes if p.status == ProcessStatus.NEW]
            if future:
                now = max(now + 1, min(future))
                continue
            now += 1
            continue

        #if the current process is gone / finished / blocked, we need to dispatch a new process
        need_dispatch = (
            current is None
            or current.status in (ProcessStatus.TERMINATED, ProcessStatus.BLOCKED)
        )

        #update the current process to the next process (using the scheduling algorithm)
        if need_dispatch:
            current = scheduler.pick_next(ready, now, current)
            #when we dispatch a new process, initialize the preemption interval using the scheduler preemptive_tick value
            if scheduler.preemptive:
                if current:
                    slice_remaining = scheduler.preempt_interval(now, current)
                else:
                    slice_remaining = None

        if current is None:
            now += 1
            continue

        #run one cycle on the current process
        print(f"Time {now}: Running {current.name} (Remaining Time: {current.remaining_time}), Algorithm: {scheduler.__class__.__name__}")
        current.run_one_cycle()
        #if the process just finished on this tick, finalize and mark TERMINATED
        if current.remaining_time == 0 and current.status == ProcessStatus.RUNNING:
            current.stop(now)

        #if the scheduler is preemptive, decrement the slice_remaining value (the time until it can preempt again)
        if scheduler.preemptive and slice_remaining is not None:
            slice_remaining -= 1

        #if the scheduling algorithm is preemptive, set the current 
        if scheduler.preemptive and current.status not in (ProcessStatus.TERMINATED, ProcessStatus.BLOCKED):
            #only force a preempt and retunr the process to ready when all of slice_time has elapsed
            #otherwise, keep the currpent process
            if slice_remaining is not None and slice_remaining <= 0:
                #return the current process to the ready state
                current.ready(now=None)
                #the scheduler has to repick the process at the next tick
                current = None
                #set the tick required to preempt the a process at the start of the next cycle
                slice_remaining = None

        now += 1
        #time.sleep(0.1) # Slow down the simulation for observability

def generate_initial_csv(processes): # Generate CSV of initial process set
    with open ("initial_processes.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Process Name", "Priority", "Arrival Time", "Service Time"])
        for p in processes:
            writer.writerow([p.name, p.priority, p.simulated_arrival_time, p.service_time])

def generate_result_csv(processes, algorithm): # Generate CSV of results after scheduling simulation
    with open (f"{algorithm}_results.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Process Name", "Priority", "Simulated Arrival Time", "Arrival Tick", "Completion Tick", "Service Time", "Turnaround (ticks)", "Waiting (ticks)"])
        for p in processes:
            ta = 0 if p.turnaround_time is None else p.turnaround_time
            wt = 0 if p.waiting_time is None else p.waiting_time
            writer.writerow([p.name, p.priority, p.simulated_arrival_time, p.arrival_tick, p.completion_tick, p.service_time, ta, wt])

def main():
    parser = argparse.ArgumentParser(description="Run ALL schedulers on a RANDOM set of processes")
    parser.add_argument("-n", type=int, default=100, help="Number of processes")
    args = parser.parse_args()

    #1. build a random set of processes of size n
    canonical = generate_processes(args.n)
    generate_initial_csv(canonical)

    #2. for each scheduler, clone the process and simulate
    for name, cls in REGISTRY.items():
        run_set = clone_processes(canonical)

        scheduler: Scheduler = cls()
        simulate(run_set, scheduler)

        generate_result_csv(run_set, name.upper())

# Just code for testing, this doesn't account for arrival time. It is a basic FIFO algorithm
# def main():
#     queue = []
#     for i in range(5):
#         p = Process(f"Process-{i+1}")
#         p.ready()
#         queue.append(p)
#     print("Initial Process Queue:")
#     for p in queue:
#         print(f"{p.name}: Status={p.status}, Priority={p.priority}, Arrival Time={p.simulated_arrival_time}, Service Time={p.service_time}")

#     for p in queue:
#         while p.status != p.status.TERMINATED:
#             p.run_one_cycle()

#     for p in queue:
#         print(f"{p.name}: Final Status={p.status}, Turnaround Time={p.turnaround_time}, Waiting Time={p.waiting_time}")

if __name__ == "__main__":
    main()
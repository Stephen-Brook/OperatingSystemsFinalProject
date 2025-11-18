from enum import Enum
import random
import time


class ProcessStatus(Enum): # Track the status of a process
    NEW = 0
    READY = 1
    RUNNING = 2
    BLOCKED = 3
    TERMINATED = 4

    def __str__(self): # String representation of the process status
        return self.name


class Process:
    def __init__(self, name):
        self.name = name
        self.id = id(self)
        self.priority = random.randint(1, 10)
        self.status = ProcessStatus.NEW
        self.simulated_arrival_time = random.randint(0, 10)
        self.service_time = random.randint(1, 10)
        self.remaining_time = self.service_time
        self.arrival_tick = None
        self.completion_tick = None
        self.turnaround_time = None
        self.waiting_time = None

    def run_one_cycle(self): # Simulate running the process for one time unit (simulated tick)
        if self.status not in (ProcessStatus.READY, ProcessStatus.RUNNING): # Check if the process is in a state that allows it to run
            #print(f"Process {self.name} cannot run. Current status: {self.status}")
            return

        self.status = ProcessStatus.RUNNING # Set the process status to RUNNING

        if self.remaining_time > 0: # If there is remaining time, simulate running
            # time.sleep(1) # Simulate the time taken for one cycle
            self.remaining_time -= 1
            #DO NOT call stop() here, we need now to compute metrics
            #the main loop will detect when remaining_time hits 0
    
    def ready(self, now=None): # Set the process status to READY using simulated time
        # Only allow transitions from NEW, BLOCKED, or RUNNING (for preemption)
        if self.status not in (ProcessStatus.NEW, ProcessStatus.BLOCKED, ProcessStatus.RUNNING):  # Check if the process can be set to READY
            #print(f"Process {self.name} cannot be set to ready. Current status: {self.status}")
            return
        else:
            #only set arrival_tick the first time it becomes READY
            if self.arrival_tick is None and now is not None:
                self.arrival_tick = now
            #print(f"Process {self.name} ready.")
            self.status = ProcessStatus.READY


    def block(self): # Set the process status to BLOCKED
        if self.status != ProcessStatus.RUNNING:
            #print(f"Process {self.name} cannot be blocked. Current status: {self.status}")
            return
        else:
            #print(f"Process {self.name} blocked. Remaining time: {self.remaining_time}")
            self.status = ProcessStatus.BLOCKED

    def stop(self, now): # terminate the process and calculate turnaround and waiting times
        if self.status != ProcessStatus.RUNNING:
            return
        else:
            self.status = ProcessStatus.TERMINATED

            #assume it completes at the END of this tick
            self.completion_tick = now + 1
            self.turnaround_time = self.completion_tick - self.arrival_tick
            self.waiting_time = self.turnaround_time - self.service_time
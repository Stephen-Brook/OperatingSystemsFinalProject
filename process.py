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
        self.real_arrival_time = None
        self.service_time = random.randint(1, 10)
        self.remaining_time = self.service_time
        self.turnaround_time = None
        self.waiting_time = None


    def run_one_cycle(self): # Simulate running the process for one time unit (1s)
        if self.status != ProcessStatus.READY and self.status != ProcessStatus.RUNNING: # Check if the process is in a state that allows it to run
            #print(f"Process {self.name} cannot run. Current status: {self.status}")
            return

        self.status = ProcessStatus.RUNNING # Set the process status to RUNNING

        if self.remaining_time > 0: # If there is remaining time, simulate running
            # time.sleep(1) # Simulate the time taken for one cycle
            self.remaining_time -= 1 # Decrease the remaining time by 1
            if self.remaining_time == 0: # If the process has completed its service time
                self.stop()
            #else: # If there is still remaining time, print the status
                #print(f"Process {self.name} running, remaining time: {self.remaining_time}")



    def ready(self): # Set the process status to READY
        if self.status != ProcessStatus.NEW and self.status != ProcessStatus.BLOCKED and self.status != ProcessStatus.RUNNING: # Check if the process can be set to READY
            #print(f"Process {self.name} cannot be set to ready. Current status: {self.status}")
            return
        else:
            if self.real_arrival_time is None: # Record the real arrival time if not already set
                self.real_arrival_time = time.time()
            #print(f"Process {self.name} ready.")
            self.status = ProcessStatus.READY


    def block(self): # Set the process status to BLOCKED
        if self.status != ProcessStatus.RUNNING:
            #print(f"Process {self.name} cannot be blocked. Current status: {self.status}")
            return
        else:
            #print(f"Process {self.name} blocked. Remaining time: {self.remaining_time}")
            self.status = ProcessStatus.BLOCKED


    def stop(self): # Terminate the process and calculate turnaround and waiting times
        if self.status != ProcessStatus.RUNNING:
            #print(f"Process {self.name} cannot be stopped. Current status: {self.status}")
            return
        else:
            self.status = ProcessStatus.TERMINATED
            self.turnaround_time = time.time() - self.real_arrival_time # Calculate turnaround time
            self.waiting_time = self.turnaround_time - self.service_time # Calculate waiting time
            #print(f"Process {self.name} terminated. Turnaround time: {self.turnaround_time}, Waiting time: {self.waiting_time}")
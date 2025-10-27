from process import Process
# Just code for testing, this doesn't account for arrival time. It is a basic FIFO algorithm
def main():
    queue = []
    for i in range(5):
        p = Process(f"Process-{i+1}")
        p.ready()
        queue.append(p)
    print("Initial Process Queue:")
    for p in queue:
        print(f"{p.name}: Status={p.status}, Priority={p.priority}, Arrival Time={p.simulated_arrival_time}, Service Time={p.service_time}")

    for p in queue:
        while p.status != p.status.TERMINATED:
            p.run_one_cycle()

    for p in queue:
        print(f"{p.name}: Final Status={p.status}, Turnaround Time={p.turnaround_time}, Waiting Time={p.waiting_time}")


if __name__ == "__main__":
    main()
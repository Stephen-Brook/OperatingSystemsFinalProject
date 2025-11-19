import csv
import matplotlib.pyplot as plt
from schedulers import REGISTRY

def run_metrics():
    algo_labels = []
    avg_turnaround_times = []
    avg_waiting_times = []

    for key in REGISTRY.keys():
        algo_name = key.upper()
        filename = f"{algo_name}_results.csv"

        try:
            avg_service, avg_turnaround, avg_waiting = _read_metrics(filename)
        except FileNotFoundError:
            print(f"Warning: {filename} not found, skipping.")
            continue

        label = key.replace("_", " ").title()
        algo_labels.append(label)
        avg_turnaround_times.append(avg_turnaround)
        avg_waiting_times.append(avg_waiting)

        print(f"{label}: TA={avg_turnaround:.2f}, wait={avg_waiting:.2f}")

    _plot_waiting(algo_labels, avg_waiting_times)
    _plot_turnaround(algo_labels, avg_turnaround_times)
    plt.show()


def _read_metrics(filename):
    total_service = 0.0
    total_turnaround = 0.0
    total_waiting = 0.0
    count = 0

    with open(filename, newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row:
                continue
            service = float(row[5])
            turnaround = float(row[6])
            waiting = float(row[7])
            total_service += service
            total_turnaround += turnaround
            total_waiting += waiting
            count += 1
    if count == 0:
        return 0.0, 0.0, 0.0
    return (total_service / count, total_turnaround / count, total_waiting / count)


def _plot_waiting(labels, waiting_values):
    x = range(len(labels))
    plt.figure(figsize=(8, 5))
    plt.bar(x, waiting_values)
    plt.xticks(x, labels)
    plt.ylabel("Average Waiting Time (ticks)")
    plt.title("Waiting Time Comparison Across Schedulers")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()


def _plot_turnaround(labels, turnaround_values):
    x = range(len(labels))
    plt.figure(figsize=(8, 5))
    plt.bar(x, turnaround_values)
    plt.xticks(x, labels)
    plt.ylabel("Average Turnaround Time (ticks)")
    plt.title("Turnaround Time Comparison Across Schedulers")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()


if __name__ == "__main__":
    run_metrics()
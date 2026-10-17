import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque

# CPU Scheduling Simulator using Tkinter

BG = "#101827"
PANEL = "#1e293b"
BLUE = "#38bdf8"

root = tk.Tk()
root.title("CPU Scheduling Simulator")
root.geometry("1000x700")
root.configure(bg=BG)

processes = []
colors = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24",
          "#fb7185", "#f97316", "#22d3ee", "#c084fc"]


def add_process():
    pid = pid_entry.get().strip()
    try:
        arrival = int(arrival_entry.get())
        burst = int(burst_entry.get())

        if not pid or arrival < 0 or burst <= 0:
            raise ValueError

        if any(p["pid"] == pid for p in processes):
            messagebox.showerror("Error", "Process ID already exists")
            return

        processes.append({
            "pid": pid, "arrival": arrival, "burst": burst
        })

        pid_entry.delete(0, tk.END)
        arrival_entry.delete(0, tk.END)
        burst_entry.delete(0, tk.END)
        update_process_table()

    except ValueError:
        messagebox.showerror(
            "Input Error",
            "Enter a unique ID, arrival >= 0, and burst > 0."
        )


def load_sample():
    processes.clear()
    processes.extend([
        {"pid": "P1", "arrival": 0, "burst": 5},
        {"pid": "P2", "arrival": 1, "burst": 3},
        {"pid": "P3", "arrival": 2, "burst": 8},
        {"pid": "P4", "arrival": 3, "burst": 2}
    ])
    update_process_table()
    run_simulation()


def update_process_table():
    for item in process_table.get_children():
        process_table.delete(item)

    for p in processes:
        process_table.insert(
            "", "end",
            values=(p["pid"], p["arrival"], p["burst"])
        )


def fcfs():
    ordered = sorted(
        processes, key=lambda p: (p["arrival"], p["pid"])
    )
    timeline = []
    results = {}
    time = 0

    for p in ordered:
        if time < p["arrival"]:
            timeline.append(("IDLE", time, p["arrival"]))
            time = p["arrival"]

        start = time
        time += p["burst"]
        timeline.append((p["pid"], start, time))

        tat = time - p["arrival"]
        results[p["pid"]] = (time, tat - p["burst"], tat)

    return timeline, results


def sjf():
    remaining = [p.copy() for p in processes]
    timeline = []
    results = {}
    time = 0

    while remaining:
        ready = [p for p in remaining if p["arrival"] <= time]

        if not ready:
            next_time = min(p["arrival"] for p in remaining)
            timeline.append(("IDLE", time, next_time))
            time = next_time
            continue

        p = min(
            ready,
            key=lambda x: (x["burst"], x["arrival"], x["pid"])
        )

        start = time
        time += p["burst"]
        timeline.append((p["pid"], start, time))

        tat = time - p["arrival"]
        results[p["pid"]] = (time, tat - p["burst"], tat)
        remaining.remove(p)

    return timeline, results


def round_robin(quantum):
    ordered = sorted(
        processes, key=lambda p: (p["arrival"], p["pid"])
    )
    remaining = {p["pid"]: p["burst"] for p in ordered}
    timeline = []
    results = {}
    queue = deque()
    i = 0
    time = 0

    while i < len(ordered) or queue:
        if not queue:
            if i < len(ordered) and time < ordered[i]["arrival"]:
                timeline.append(("IDLE", time, ordered[i]["arrival"]))
                time = ordered[i]["arrival"]

            while i < len(ordered) and ordered[i]["arrival"] <= time:
                queue.append(ordered[i]["pid"])
                i += 1

        if not queue:
            continue

        pid = queue.popleft()
        start = time
        duration = min(quantum, remaining[pid])
        time += duration
        remaining[pid] -= duration
        timeline.append((pid, start, time))

        while i < len(ordered) and ordered[i]["arrival"] <= time:
            queue.append(ordered[i]["pid"])
            i += 1

        if remaining[pid] > 0:
            queue.append(pid)
        else:
            p = next(p for p in ordered if p["pid"] == pid)
            tat = time - p["arrival"]
            results[pid] = (time, tat - p["burst"], tat)

    return timeline, results


def run_simulation():
    if not processes:
        messagebox.showwarning("Notice", "Add processes first.")
        return

    algorithm = algo_box.get()

    if algorithm == "FCFS":
        timeline, results = fcfs()
    elif algorithm == "SJF":
        timeline, results = sjf()
    else:
        try:
            quantum = int(quantum_entry.get())
            if quantum <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error", "Time quantum must be a positive integer."
            )
            return
        timeline, results = round_robin(quantum)

    show_results(timeline, results)


def show_results(timeline, results):
    for item in result_table.get_children():
        result_table.delete(item)

    waits = []
    turnarounds = []

    for p in sorted(processes, key=lambda x: x["pid"]):
        completion, waiting, turnaround = results[p["pid"]]
        waits.append(waiting)
        turnarounds.append(turnaround)

        result_table.insert(
            "", "end",
            values=(
                p["pid"], p["arrival"], p["burst"],
                completion, waiting, turnaround
            )
        )

    avg_wait = sum(waits) / len(waits)
    avg_tat = sum(turnarounds) / len(turnarounds)
    total_time = max(end for _, _, end in timeline)

    stats_label.config(
        text=f"Processes: {len(processes)}     "
             f"Average Waiting: {avg_wait:.2f}     "
             f"Average Turnaround: {avg_tat:.2f}     "
             f"Total CPU Time: {total_time}"
    )

    draw_gantt(timeline)


def draw_gantt(timeline):
    canvas.delete("all")

    if not timeline:
        return

    canvas.update_idletasks()
    width = max(canvas.winfo_width(), 700)
    start_time = min(start for _, start, _ in timeline)
    end_time = max(end for _, _, end in timeline)
    duration = end_time - start_time

    if duration <= 0:
        return

    left = 30
    right = width - 30
    scale = (right - left) / duration
    y1, y2 = 25, 75

    pid_list = sorted(p["pid"] for p in processes)

    for pid, start, end in timeline:
        x1 = left + (start - start_time) * scale
        x2 = left + (end - start_time) * scale

        if pid == "IDLE":
            color = "#64748b"
        else:
            color = colors[pid_list.index(pid) % len(colors)]

        canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=color, outline=BG, width=2
        )

        if x2 - x1 >= 25:
            canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2,
                text=pid, fill="#101827",
                font=("Arial", 10, "bold")
            )

        canvas.create_text(
            x1, 95, text=str(start),
            fill="white", font=("Arial", 9)
        )

    canvas.create_text(
        right, 95, text=str(end_time),
        fill="white", font=("Arial", 9)
    )


def reset_all():
    processes.clear()
    update_process_table()

    for item in result_table.get_children():
        result_table.delete(item)

    canvas.delete("all")
    stats_label.config(text="Add processes and run a simulation.")


# ---------------- Dashboard UI ----------------

tk.Label(
    root, text="CPU SCHEDULING SIMULATOR",
    font=("Arial", 23, "bold"), bg=BG, fg=BLUE
).pack(pady=(15, 3))

tk.Label(
    root, text="FCFS  |  SJF  |  ROUND ROBIN",
    font=("Arial", 11), bg=BG, fg="white"
).pack(pady=(0, 12))

input_frame = tk.Frame(root, bg=PANEL, padx=10, pady=10)
input_frame.pack(fill="x", padx=20)

tk.Label(input_frame, text="Process ID", bg=PANEL, fg="white").grid(
    row=0, column=0, padx=5
)
pid_entry = ttk.Entry(input_frame, width=12)
pid_entry.grid(row=1, column=0, padx=5)

tk.Label(input_frame, text="Arrival Time", bg=PANEL, fg="white").grid(
    row=0, column=1, padx=5
)
arrival_entry = ttk.Entry(input_frame, width=12)
arrival_entry.grid(row=1, column=1, padx=5)

tk.Label(input_frame, text="Burst Time", bg=PANEL, fg="white").grid(
    row=0, column=2, padx=5
)
burst_entry = ttk.Entry(input_frame, width=12)
burst_entry.grid(row=1, column=2, padx=5)

tk.Button(
    input_frame, text="Add Process", command=add_process,
    bg=BLUE, fg="#101827"
).grid(row=1, column=3, padx=8)

tk.Button(
    input_frame, text="Load Sample", command=load_sample
).grid(row=1, column=4, padx=5)

tk.Button(
    input_frame, text="Reset", command=reset_all
).grid(row=1, column=5, padx=5)

control_frame = tk.Frame(root, bg=BG)
control_frame.pack(fill="x", padx=25, pady=12)

tk.Label(
    control_frame, text="Algorithm:", bg=BG, fg="white"
).pack(side="left")

algo_box = ttk.Combobox(
    control_frame, values=["FCFS", "SJF", "Round Robin"],
    state="readonly", width=15
)
algo_box.set("FCFS")
algo_box.pack(side="left", padx=8)

tk.Label(
    control_frame, text="Time Quantum:", bg=BG, fg="white"
).pack(side="left", padx=(10, 3))

quantum_entry = ttk.Entry(control_frame, width=6)
quantum_entry.insert(0, "2")
quantum_entry.pack(side="left")

tk.Button(
    control_frame, text="RUN SIMULATION",
    command=run_simulation, bg="#16a34a", fg="white"
).pack(side="right")

tk.Label(
    root, text="PROCESS INPUT TABLE",
    bg=BG, fg=BLUE, font=("Arial", 11, "bold")
).pack(anchor="w", padx=25)

process_table = ttk.Treeview(
    root, columns=("pid", "arrival", "burst"),
    show="headings", height=4
)

for col, title in [
    ("pid", "Process ID"),
    ("arrival", "Arrival Time"),
    ("burst", "Burst Time")
]:
    process_table.heading(col, text=title)
    process_table.column(col, anchor="center", width=150)

process_table.pack(fill="x", padx=25, pady=5)

tk.Label(
    root, text="CPU GANTT CHART",
    bg=BG, fg=BLUE, font=("Arial", 11, "bold")
).pack(anchor="w", padx=25, pady=(8, 0))

canvas = tk.Canvas(root, height=115, bg=PANEL, highlightthickness=0)
canvas.pack(fill="x", padx=25, pady=5)

stats_label = tk.Label(
    root, text="Add processes and run a simulation.",
    bg=BG, fg="#34d399", font=("Arial", 10, "bold")
)
stats_label.pack(pady=5)

tk.Label(
    root, text="PROCESS RESULTS",
    bg=BG, fg=BLUE, font=("Arial", 11, "bold")
).pack(anchor="w", padx=25, pady=(5, 0))

result_table = ttk.Treeview(
    root,
    columns=("pid", "arrival", "burst", "completion",
             "waiting", "turnaround"),
    show="headings", height=5
)

for col, title in [
    ("pid", "Process"),
    ("arrival", "Arrival"),
    ("burst", "Burst"),
    ("completion", "Completion"),
    ("waiting", "Waiting Time"),
    ("turnaround", "Turnaround Time")
]:
    result_table.heading(col, text=title)
    result_table.column(col, anchor="center", width=135)

result_table.pack(fill="both", expand=True, padx=25, pady=(5, 15))

load_sample()
root.mainloop()
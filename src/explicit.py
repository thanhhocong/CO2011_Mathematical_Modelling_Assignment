# src/explicit.py
from collections import deque
from petri_net import PetriNet
import time
import psutil
import os

def explicit_reachability(net: PetriNet):
    process = psutil.Process(os.getpid())
    start_time = time.time()

    initial = net.marking_to_tuple(net.initial_marking)
    queue = deque([initial])
    visited = {initial}

    while queue:
        current = queue.popleft()
        marking = net.tuple_to_marking(current)
        for t in net.transitions:
            if net.is_enabled(t, marking):
                next_m = net.fire(t, marking)
                next_t = net.marking_to_tuple(next_m)
                if next_t not in visited:
                    visited.add(next_t)
                    queue.append(next_t)

    end_time = time.time()
    memory = process.memory_info().rss / 1024 / 1024

    print(f"[Explicit] Reachable: {len(visited)} | Time: {end_time-start_time:.3f}s | Mem: {memory:.1f}MB")
    return visited
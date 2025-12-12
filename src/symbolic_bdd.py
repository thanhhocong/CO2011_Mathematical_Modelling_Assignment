# src/symbolic_bdd.py
from dd.autoref import BDD
from petri_net import PetriNet
import time
import psutil
import os

def symbolic_reachability(net: PetriNet):
    bdd = BDD()
    for i in range(len(net.place_order)):
        bdd.declare(f'x{i}')

    def encode_marking(marking):
        clauses = []
        for i, p in enumerate(net.place_order):
            val = marking.get(p, 0)
            clauses.append(f'x{i}' if val > 0 else f'~x{i}')
        return ' & '.join(clauses) if clauses else '1'

    def transition_relation(t):
        pre_conds = [f'x{i}' for i, p in enumerate(net.place_order) if p in net.pre[t]]
        unchanged = [f'(x{i} <=> x{i}_)' for i, p in enumerate(net.place_order) if p not in net.pre[t] and p not in net.post[t]]
        to_zero = [f'~x{i}_' for i, p in enumerate(net.place_order) if p in net.pre[t] and p not in net.post[t]]
        to_one = [f'x{i}_' for i, p in enumerate(net.place_order) if p not in net.pre[t] and p in net.post[t]]
        both = [f'(x{i} <=> x{i}_)' for i, p in enumerate(net.place_order) if p in net.pre[t] and p in net.post[t]]
        pre_expr = ' & '.join(pre_conds) if pre_conds else '1'
        body = ' & '.join(unchanged + both + to_zero + to_one)
        return f'({pre_expr}) & ({body})' if body else pre_expr

    primed_vars = [f'x{i}_' for i in range(len(net.place_order))]
    bdd.declare(*primed_vars)

    R = bdd.false
    for t in net.transitions:
        expr = transition_relation(t)
        Rt = bdd.add_expr(expr)
        R |= Rt

    S = bdd.add_expr(encode_marking(net.initial_marking))

    process = psutil.Process(os.getpid())
    start_time = time.time()
    iteration = 0
    while True:
        iteration += 1
        f = S & R
        img_prime = bdd.exist(
            [f'x{i}' for i in range(len(net.place_order))],
            f
        )
        renaming = {f'x{i}_': f'x{i}' for i in range(len(net.place_order))}
        img = bdd.let(renaming, img_prime)
        S_new = S | img
        if S_new == S:
            break
        S = S_new

    end_time = time.time()
    count = sum(1 for _ in bdd.pick_iter(S))
    memory = process.memory_info().rss / 1024 / 1024

    print(f"[BDD] Reachable markings: {count}")
    print(f"[BDD] Iterations: {iteration} | Time: {end_time-start_time:.3f}s | Mem: {memory:.1f}MB")
    return bdd, S
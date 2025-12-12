# src/optimize_ilp.py
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpBinary, LpStatus, PULP_CBC_CMD
from petri_net import PetriNet

def optimize_reachable(net: PetriNet, bdd, S, c: dict):
    print("[OPT] Searching optimal marking in reachable set...")
    prob = LpProblem("Optimize_Reachable", LpMaximize)

    # Variables for firing counts (sigma) and markings (m)
    sigma = {t: LpVariable(f"sigma_{t}", lowBound=0, cat='Integer') for t in net.transitions}
    m = {p: LpVariable(f"m_{p}", cat=LpBinary) for p in net.places}

    # State equation constraints
    for p in net.places:
        pre_t = [t for t in net.transitions if p in net.pre[t]]
        post_t = [t for t in net.transitions if p in net.post[t]]
        prob += m[p] == net.initial_marking[p] + lpSum(sigma[t] for t in post_t) - lpSum(sigma[t] for t in pre_t), f"state_{p}"

    # Objective: Maximize the weighted sum
    prob += lpSum(c.get(p, 0) * m[p] for p in net.places)

    cut_count = 0
    while True:
        status = prob.solve(PULP_CBC_CMD(msg=0))  # Sửa: tắt verbose log
        if LpStatus[status] != 'Optimal':
            print("[OPT] No feasible solution found.")
            return None

        marking = {p: int(m[p].value()) for p in net.places}
        value = sum(c.get(p, 0) * marking[p] for p in net.places)

        # Encode marking as BDD expression for verification
        clauses = []
        for i, p in enumerate(net.place_order):
            val = marking[p]
            clauses.append(f'x{i}' if val > 0 else f'~x{i}')
        expr = ' & '.join(clauses) if clauses else '1'
        m_bdd = bdd.add_expr(expr)

        # Check if the marking is truly reachable using the BDD
        if (S & m_bdd) != bdd.false:
            if cut_count > 0:
                print(f"[OPT] Added {cut_count} cuts to exclude spurious markings.")
            print(f"[OPT] Optimal marking: {marking} | Value: {value}")
            return marking
        else:
            cut_count += 1
            # Add cutting plane to exclude this spurious marking
            cut = lpSum((1 - m[p]) for p in net.places if marking[p] == 1) + lpSum(m[p] for p in net.places if marking[p] == 0) >= 1
            prob += cut, f"cut{cut_count}"
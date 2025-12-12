# src/deadlock_ilp.py
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus, PULP_CBC_CMD
from petri_net import PetriNet

def find_deadlock(net: PetriNet, bdd, S):
    print("[ILP] Checking for deadlock in reachable states...")
    prob = LpProblem("Deadlock_Detection", LpMinimize)

    # Variables for firing counts (sigma) and markings (m)
    sigma = {t: LpVariable(f"sigma_{t}", lowBound=0, cat='Integer') for t in net.transitions}
    m = {p: LpVariable(f"m_{p}", cat=LpBinary) for p in net.places}

    # State equation constraints
    for p in net.places:
        pre_t = [t for t in net.transitions if p in net.pre[t]]
        post_t = [t for t in net.transitions if p in net.post[t]]
        prob += m[p] == net.initial_marking[p] + lpSum(sigma[t] for t in post_t) - lpSum(sigma[t] for t in pre_t), f"state_{p}"

    # Deadlock conditions (no transition enabled)
    for t in net.transitions:
        if net.pre[t]:
            prob += lpSum(m[p] for p in net.pre[t]) <= len(net.pre[t]) - 1, f"dead_{t}"

    # Dummy objective for feasibility
    prob += 0

    cut_count = 0
    while True:
        status = prob.solve(PULP_CBC_CMD(msg=0))  # Sửa: tắt verbose log
        if LpStatus[status] != 'Optimal':
            print("[ILP] No deadlock found.")
            return None

        marking = {p: int(m[p].value()) for p in net.places}

        # Encode marking as BDD expression for verification
        clauses = []
        for i, p in enumerate(net.place_order):
            val = marking[p]
            clauses.append(f'x{i}' if val > 0 else f'~x{i}')
        expr = ' & '.join(clauses) if clauses else '1'
        m_bdd = bdd.add_expr(expr)

        # Check if the marking is truly reachable using the BDD
        if (S & m_bdd) != bdd.false:
            print(f"[ILP] DEADLOCK FOUND: {marking}")
            return marking
        else:
            print(f"[ILP] Spurious marking found, adding cut to exclude it.")
            cut_count += 1
            # Add cutting plane to exclude this spurious marking
            cut = lpSum((1 - m[p]) for p in net.places if marking[p] == 1) + lpSum(m[p] for p in net.places if marking[p] == 0) >= 1
            prob += cut, f"cut{cut_count}"
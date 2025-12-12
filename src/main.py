# main.py
import inspect
import sys
import os
# Add src directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Redirect stderr to null to suppress benign exceptions
import io
original_stderr = sys.stderr
sys.stderr = io.StringIO()  # Suppress all stderr output

from parser import parse_pnml
from explicit import explicit_reachability
from symbolic_bdd import symbolic_reachability
from deadlock_ilp import find_deadlock
from optimize_ilp import optimize_reachable


if __name__ == "__main__":
    print("=== CO2011 - Petri Net Analysis ===\n")
    
    # Chọn file
    # file = "pnml/philosopher_deadlock.pnml"
    file = "pnml/deadlock_chain.pnml"
    net = parse_pnml(file)
    print(f"Loaded: {len(net.places)} places, {len(net.transitions)} transitions")
    print(f"Initial marking: {net.initial_marking}\n")

    print("--- TASK 2: Explicit Reachability ---")
    explicit_reachability(net)
    
    print("\n--- TASK 3: Symbolic Reachability (BDD) ---")
    bdd, S = symbolic_reachability(net)

    print("\n--- TASK 4: Deadlock Detection (ILP + BDD) ---")
    find_deadlock(net, bdd, S)

    print("\n--- TASK 5: Optimization over Reachable Markings ---")
    c = {p: 1 for p in net.places}  # maximize total tokens
    optimize_reachable(net, bdd, S, c)

import warnings, dd

# Suppress destructor warnings from dd.bdd.BDD at program exit
warnings.filterwarnings("ignore", category=ResourceWarning)
dd.bdd.BDD.__del__ = lambda self: None

    # Optional: Reset stderr if needed (e.g., for debug)
    # sys.stderr = original_stderr
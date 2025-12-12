# CO2011 - Petri Net Analysis Project
## Abstract

This project implements a comprehensive suite of Petri Net analysis tools for 1-safe Petri nets. The implementation includes five major components: (1) a PNML parser for reading standard Petri net files, (2) explicit state-space exploration using breadth-first search, (3) symbolic reachability analysis using Binary Decision Diagrams (BDDs), (4) deadlock detection combining Integer Linear Programming (ILP) with BDD-based reachability, and (5) optimization over reachable markings. The system demonstrates the trade-offs between explicit and symbolic approaches and showcases how hybrid ILP+BDD methods can efficiently solve verification problems.

---

## Installation and Usage

### Project Structure

```
./
├── pnml/                      # Test models
│   ├── deadlock_chain.pnml
│   ├── parallel_branch.pnml
│   ├── philosopher_deadlock.pnml
│   ├── producer_consumer.pnml
│   ├── shared_resource.pnml
│   └── simple_line.pnml
├── src/                       # Source code
│   ├── __init__.py
│   ├── petri_net.py          # Core data structure
│   ├── parser.py             # Task 1: PNML parser
│   ├── explicit.py           # Task 2: Explicit reachability
│   ├── symbolic_bdd.py       # Task 3: Symbolic reachability
│   ├── deadlock_ilp.py       # Task 4: Deadlock detection
│   ├── optimize_ilp.py       # Task 5: Optimization
│   ├── main.py               # Main entry point
│   └── requirements.txt      # Dependencies
└─── README.md                  # This file
```

### Installation Steps

1. **Install Dependencies:**
   ```
   pip install -r src/requirements.txt
   ```

   Dependencies include:
   - `dd>=0.2.0` - Binary Decision Diagram library
   - `pulp>=2.7` - Linear programming solver
   - `lxml>=4.9` - XML parsing
   - `psutil>=5.9` - System resource monitoring

2. **Verify Installation:**
   ```bash
   python -c "import dd, pulp, lxml, psutil; print('All dependencies installed!')"
   ```

### Running the Analysis

#### Basic Usage

1. **Select a test model** by editing `src/main.py`:
   ```python
   # Line 24-25 in main.py
   # file = "pnml/philosopher_deadlock.pnml"
   file = "pnml/deadlock_chain.pnml"  # Change this line
   ```

2. **Run all analyses:**
   ```bash
   python src/main.py
   ```

3. **Expected output:**
   ```
   === CO2011 - Petri Net Analysis ===
   
   Loaded: 4 places, 2 transitions
   Initial marking: {'a': 1, 'b': 1, 'r1': 1, 'r2': 1}
   
   --- TASK 2: Explicit Reachability ---
   [Explicit] Reachable: 2 | Time: 0.000s | Mem: 43.8MB
   
   --- TASK 3: Symbolic Reachability (BDD) ---
   [BDD] Reachable markings: 2
   [BDD] Iterations: 2 | Time: 0.000s | Mem: 44.3MB
   
   --- TASK 4: Deadlock Detection (ILP + BDD) ---
   [ILP] Checking for deadlock in reachable states...
   [ILP] DEADLOCK FOUND: {'a': 1, 'b': 1, 'r1': 0, 'r2': 0}
   
   --- TASK 5: Optimization over Reachable Markings ---
   [OPT] Searching optimal marking in reachable set...
   [OPT] Optimal marking: {'a': 1, 'b': 1, 'r1': 1, 'r2': 1} | Value: 4
   ```

#### Custom Objective Functions

To change the optimization objective in Task 5, modify line 40 in `src/main.py`:

```python
# Example 1: Maximize total tokens (default)
c = {p: 1 for p in net.places}

# Example 2: Maximize tokens in specific places
c = {'p1': 2, 'p2': 1, 'p3': 0}  # Prioritize p1, then p2, ignore p3

# Example 3: Minimize tokens (use negative weights)
c = {p: -1 for p in net.places}
```

#### Individual Task Execution

To run only specific tasks, comment out unwanted sections in `src/main.py`:

```python
# Run only explicit reachability
print("--- TASK 2: Explicit Reachability ---")
explicit_reachability(net)

# Comment out others:
# print("\n--- TASK 3: Symbolic Reachability (BDD) ---")
# bdd, S = symbolic_reachability(net)
# ...
```

### Creating Custom Test Cases

1. **Create a new PNML file** in the `pnml/` directory:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <pnml xmlns="http://www.pnml.org/version-2009/grammar/pnmlcoremodel">
     <net id="my_net" type="http://www.pnml.org/version-2009/grammar/ptnet">
       <page id="page1">
         <!-- Define places -->
         <place id="p1">
           <name><text>Place1</text></name>
           <initialMarking><text>1</text></initialMarking>
         </place>
         
         <!-- Define transitions -->
         <transition id="t1">
           <name><text>Transition1</text></name>
         </transition>
         
         <!-- Define arcs -->
         <arc source="p1" target="t1"/>
         <arc source="t1" target="p2"/>
       </page>
     </net>
   </pnml>
   ```

2. **Update main.py** to use your model:
   ```python
   file = "pnml/my_net.pnml"
   ```

3. **Run the analysis:**
   ```bash
   python src/main.py
   ```
   ---

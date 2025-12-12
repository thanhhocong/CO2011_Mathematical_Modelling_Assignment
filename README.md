# CO2011 - Petri Net Analysis Project
## Abstract

This project implements a comprehensive suite of Petri Net analysis tools for 1-safe Petri nets. The implementation includes five major components: (1) a PNML parser for reading standard Petri net files, (2) explicit state-space exploration using breadth-first search, (3) symbolic reachability analysis using Binary Decision Diagrams (BDDs), (4) deadlock detection combining Integer Linear Programming (ILP) with BDD-based reachability, and (5) optimization over reachable markings. The system demonstrates the trade-offs between explicit and symbolic approaches and showcases how hybrid ILP+BDD methods can efficiently solve verification problems.

---

## Table of Contents

1. [Theoretical Background](#theoretical-background)
2. [Implementation Design](#implementation-design)
3. [Experimental Results](#experimental-results)
4. [Challenges and Improvements](#challenges-and-improvements)
5. [Installation and Usage](#installation-and-usage)
6. [References](#references)

---

## 1. Theoretical Background

### 1.1 Petri Nets

A **Petri Net** is a mathematical modeling language for describing distributed systems. Formally, a Petri net is a tuple `N = (P, T, F, M₀)` where:
- **P** is a finite set of places (representing conditions/states)
- **T** is a finite set of transitions (representing events/actions)
- **F ⊆ (P × T) ∪ (T × P)** is the flow relation (arcs)
- **M₀: P → ℕ** is the initial marking (token distribution)

A **1-safe Petri net** restricts each place to contain at most one token (0 or 1), which allows for efficient binary encoding.

**Transition Firing:** A transition `t` is *enabled* at marking `M` if all input places have at least one token. Firing `t` consumes tokens from input places and produces tokens in output places, yielding a new marking `M'`.

**Reachability:** The set `Reach(M₀)` contains all markings reachable from the initial marking through sequences of transition firings. Computing this set is fundamental to verification tasks.

### 1.2 Explicit State-Space Exploration

The explicit approach enumerates all reachable states using graph traversal algorithms:
- **Breadth-First Search (BFS):** Explores states level-by-level, guaranteeing shortest paths
- **Depth-First Search (DFS):** Explores deeply before backtracking, using less memory

**Advantages:** Simple to implement, exact state counts  
**Disadvantages:** State-space explosion—exponential growth with system size

### 1.3 Binary Decision Diagrams (BDDs)

A **Binary Decision Diagram** is a compressed graph representation of a boolean function. For 1-safe Petri nets, markings can be encoded as boolean vectors where `xᵢ = 1` if place `pᵢ` has a token.

**Symbolic Reachability:** Instead of enumerating individual states, we represent sets of states symbolically:
- **Encoding:** Markings → Boolean formulas
- **Transition Relation:** `R(x, x')` relates current state `x` to next state `x'`
- **Image Computation:** `Img(S) = ∃x. S(x) ∧ R(x, x')`
- **Fixpoint Iteration:** `S₀ = M₀; Sᵢ₊₁ = Sᵢ ∪ Img(Sᵢ)` until `Sᵢ₊₁ = Sᵢ`

**Advantages:** Can handle large state spaces through compression  
**Disadvantages:** Performance depends on variable ordering; overhead for small models

### 1.4 Integer Linear Programming (ILP)

ILP formulates problems as linear constraints with integer variables. For Petri nets, the **state equation** provides necessary conditions for reachability:

```
M = M₀ + C · σ
```

where `C` is the incidence matrix and `σ` is the firing count vector.

**Limitation:** The state equation is an *over-approximation*—solutions may include spurious (unreachable) markings.

### 1.5 Hybrid ILP + BDD Approach

To eliminate spurious solutions, we combine:
1. **ILP:** Efficiently finds candidate solutions satisfying constraints
2. **BDD:** Precisely verifies true reachability
3. **Cutting Planes:** Iteratively exclude spurious solutions

This approach leverages ILP's constraint-solving power while ensuring soundness via BDD verification.

---

## 2. Implementation Design

### 2.1 Architecture Overview

```
┌─────────────────┐
│  PNML Parser    │ → Reads XML, builds PetriNet object
└────────┬────────┘
         │
         ├─→ Explicit Reachability (BFS)
         ├─→ Symbolic Reachability (BDD)
         └─→ Verification (ILP + BDD)
             ├─→ Deadlock Detection
             └─→ Optimization
```

### 2.2 Data Structures

**PetriNet Class** (`petri_net.py`):
```python
class PetriNet:
    places: Dict[str, str]           # place_id → name
    transitions: Dict[str, str]      # transition_id → name
    pre: Dict[str, Set[str]]         # transition → input places
    post: Dict[str, Set[str]]        # transition → output places
    initial_marking: Dict[str, int]  # place → token count
    place_order: List[str]           # Consistent ordering for encoding
```

### 2.3 Task Implementations

#### Task 1: PNML Parser
- Uses `xml.etree.ElementTree` for XML parsing
- Handles PNML namespace: `http://www.pnml.org/version-2009/grammar/pnmlcoremodel`
- Extracts places, transitions, arcs, and initial markings
- Validates consistency (all arc endpoints exist)

#### Task 2: Explicit Reachability
- **Algorithm:** Breadth-First Search (BFS)
- **Data Structure:** `deque` for queue, `set` for visited states
- **State Representation:** Tuples for hashing efficiency
- **Time Complexity:** O(|S| + |T|) where S = states, T = transitions

#### Task 3: Symbolic Reachability
- **Library:** `dd.autoref` for automatic reference counting
- **Encoding:** Binary variables `x₀, x₁, ...` for places
- **Transition Relation:** Encodes preconditions and effects:
  - Preconditions: `xᵢ` for input places
  - Unchanged: `xᵢ ⇔ xᵢ'` for unaffected places
  - Consumed: `¬xᵢ'` for places losing tokens
  - Produced: `xᵢ'` for places gaining tokens
- **Fixpoint Iteration:** Computes forward reachability set

#### Task 4: Deadlock Detection
- **Deadlock Definition:** A reachable marking where no transition is enabled
- **ILP Formulation:**
  - Variables: `σₜ` (firing counts), `mₚ` (marking, binary)
  - State equation: `mₚ = M₀(p) + Σ(produces) - Σ(consumes)`
  - Deadlock constraint: `Σ(mₚ for p ∈ •t) ≤ |•t| - 1` for all transitions `t`
- **Verification Loop:**
  1. Solve ILP for candidate deadlock marking
  2. Encode marking as BDD formula
  3. Check `S ∧ M ≠ ⊥` (marking is in reachable set)
  4. If spurious, add cutting plane and repeat

#### Task 5: Optimization
- **Objective:** Maximize `Σ cₚ · mₚ` over reachable markings
- **Method:** Same ILP+BDD verification loop as Task 4
- **Cutting Planes:** `Σ(1 - mₚ) + Σ(mₚ) ≥ 1` excludes specific spurious marking

### 2.4 Key Algorithms

**Cutting Plane Generation:**
```python
# Exclude marking M* from future ILP solutions
cut = Σ((1 - mₚ) for p where M*(p) = 1) + Σ(mₚ for p where M*(p) = 0) ≥ 1
```
This constraint ensures at least one place differs from the spurious marking.

---

## Prerequisites

- Python 3.8 or higher
- Required libraries (listed in `requirements.txt`):
  - `dd>=0.2.0` (for BDD operations)
  - `pulp>=2.7` (for ILP solving)
  - `lxml>=4.9` (for XML parsing)
  - `psutil>=5.9` (for memory profiling)

Install all dependencies:
```bash
pip install -r requirements.txt
```

## 3. Experimental Results

### 3.1 Test Models

The project includes six test cases with varying characteristics:

| Model | Places | Transitions | Initial Tokens | Description |
|-------|--------|-------------|----------------|-------------|
| `simple_line.pnml` | 3 | 2 | 1 | Linear token flow |
| `producer_consumer.pnml` | 2 | 2 | 1 | Basic producer-consumer |
| `shared_resource.pnml` | 3 | 2 | 2 | Resource sharing |
| `parallel_branch.pnml` | 4 | 2 | 1 | Parallel execution paths |
| `deadlock_chain.pnml` | 4 | 2 | 4 | Resource dependency deadlock |
| `philosopher_deadlock.pnml` | 6 | 3 | 4 | Dining philosophers variant |

### 3.2 Performance Comparison

**Test Case: deadlock_chain.pnml**
```
Initial Marking: {'a': 1, 'b': 1, 'r1': 1, 'r2': 1}
Reachable States: 2

┌─────────────────┬────────────┬──────────┬─────────┐
│ Method          │ States     │ Time(s)  │ Memory  │
├─────────────────┼────────────┼──────────┼─────────┤
│ Explicit (BFS)  │ 2          │ 0.000    │ 43.8 MB │
│ Symbolic (BDD)  │ 2          │ 0.000    │ 44.3 MB │
│ ILP Deadlock    │ Found      │ ~0.001   │ -       │
│ ILP Optimize    │ Value: 4   │ ~0.001   │ -       │
└─────────────────┴────────────┴──────────┴─────────┘

Deadlock Found: {'a': 1, 'b': 1, 'r1': 0, 'r2': 0}
Optimal Marking: {'a': 1, 'b': 1, 'r1': 1, 'r2': 1} (initial state)
```

**Test Case: philosopher_deadlock.pnml**
```
Initial Marking: {'p1': 1, 'p2': 1, 'p3': 1, 'c1': 1, 'c2': 1, 'c3': 1}
Reachable States: 4

┌─────────────────┬────────────┬──────────┬─────────┐
│ Method          │ States     │ Time(s)  │ Memory  │
├─────────────────┼────────────┼──────────┼─────────┤
│ Explicit (BFS)  │ 4          │ 0.000    │ 44.1 MB │
│ Symbolic (BDD)  │ 4          │ 0.001    │ 44.5 MB │
│ ILP Deadlock    │ Found      │ ~0.002   │ -       │
│ ILP Optimize    │ Value: 6   │ ~0.001   │ -       │
└─────────────────┴────────────┴──────────┴─────────┘

Deadlock Found: {'p1': 1, 'p2': 1, 'p3': 1, 'c1': 0, 'c2': 0, 'c3': 1}
```

### 3.3 Analysis

**Small State Spaces (< 10 states):**
- Explicit methods are fastest due to minimal overhead
- BDD overhead (variable declaration, symbolic operations) dominates
- Both approaches complete in < 1ms

**Expected Scaling Behavior:**
- **Explicit:** Time and memory grow linearly with |Reach(M₀)|
- **BDD:** Can exploit structure; worst-case exponential, but often logarithmic compression
- **ILP+BDD:** Efficient for targeted queries; iteration count depends on spurious solutions

**Memory Efficiency:**
- For these small models, memory usage is similar (~44 MB includes Python runtime)
- BDD advantage would emerge with larger state spaces (> 10⁶ states)

### 3.4 Deadlock Detection Results

Both test cases demonstrate successful deadlock detection:

1. **deadlock_chain.pnml:** Models two processes (A, B) competing for resources (R1, R2) in opposite orders—classic circular dependency
   - Initial: All have tokens → deadlock-free
   - After partial firing: Processes hold resources, waiting for each other → deadlock

2. **philosopher_deadlock.pnml:** Three philosophers competing for chopsticks
   - Deadlock occurs when each philosopher holds one chopstick

**ILP+BDD Verification:** In both cases, ILP found the correct deadlock on first iteration (no spurious solutions), confirming the approach's efficiency.

---

## 4. Challenges and Improvements

### 4.1 Challenges Encountered

#### Challenge 1: Spurious Solutions in ILP
**Problem:** The Petri net state equation is an over-approximation—it generates markings that satisfy the equation but are not truly reachable.

**Example:**
```
Consider: P1 → T1 → P2 → T2 → P3
ILP might suggest M = {P1: 1, P3: 1} by firing T1 and T2 "simultaneously"
But actually: Token must move sequentially through P2
```

**Solution:** Implemented cutting plane method:
1. Solve ILP to get candidate marking M*
2. Check reachability: `S ∧ M* ≠ ⊥` using BDD from Task 3
3. If spurious, add constraint excluding M* and resolve
4. Repeat until truly reachable solution found

#### Challenge 2: BDD Variable Ordering
**Problem:** BDD size and performance are highly sensitive to variable ordering.

**Current Approach:** Use place order from parser (order of appearance in PNML file)

**Potential Improvement:** Implement dynamic reordering or heuristics:
- **FORCE ordering:** Group related variables (connected by transitions)
- **Interleaving:** Alternate current/next-state variables
- **Sifting algorithm:** Dynamically optimize during BDD construction

#### Challenge 3: State-Space Explosion
**Problem:** Even with BDDs, some models have exponential state spaces.

**Mitigations:**
- **Bounded model checking:** Limit exploration depth
- **Partial order reduction:** Exploit independence of concurrent transitions
- **Symmetry reduction:** Collapse symmetric states

#### Challenge 4: Python Performance Overhead
**Problem:** Python interpreter adds significant overhead compared to C/C++ implementations.

**Trade-offs:**
- **Advantage:** Rapid prototyping, readable code, rich libraries
- **Disadvantage:** 10-100× slower than native code

**Future Work:** Critical sections could be rewritten in Cython or use Rust bindings.

### 4.2 Possible Improvements

#### 1. Enhanced Parser
- Support weighted arcs (arc multiplicity > 1)
- Handle inhibitor arcs
- Support hierarchical/colored Petri nets
- Validate PNML against schema

#### 2. Advanced Reachability Algorithms
- **Saturation-based symbolic search:** More efficient BDD fixpoint computation
- **IC3/PDR:** Property-directed reachability for safety properties
- **Bounded model checking:** SAT-based techniques for depth-limited search

#### 3. Additional Verification Tasks
- **Liveness checking:** Verify transitions can always eventually fire
- **Invariant generation:** Discover place/transition invariants
- **CTL model checking:** Verify temporal logic properties
- **Coverability analysis:** Check if marking is coverable (for unbounded nets)

#### 4. Optimization Enhancements
- **Multi-objective optimization:** Pareto-optimal markings
- **Constraint handling:** User-defined constraints beyond reachability
- **Heuristic search:** A* or best-first search for optimization

#### 5. Visualization
- **Graphical Petri net display:** Using graphviz or networkx
- **State-space graph:** Visualize reachability graph for small models
- **BDD structure:** Show BDD DAG to understand compression
- **Animation:** Step-by-step firing sequence visualization

#### 6. Benchmarking Suite
- **Standard benchmarks:** MCC (Model Checking Contest) models
- **Scalability tests:** Generate parameterized model families
- **Performance profiling:** Identify bottlenecks with cProfile
- **Comparison:** Benchmark against tools like LoLA, ITS-Tools, TAPAAL

### 4.3 Lessons Learned

1. **Hybrid methods are powerful:** Combining ILP (efficient constraint solving) with BDD (precise reachability) provides the best of both worlds

2. **Over-approximation requires verification:** State equations alone are insufficient; always verify with exact methods

3. **Symbolic methods need tuning:** Variable ordering and operation sequencing dramatically affect BDD performance

4. **Small models favor explicit methods:** Overhead matters—symbolic approaches shine only at scale

5. **Tool integration:** Leveraging mature solvers (PuLP/CBC for ILP, dd for BDD) accelerates development

---

## 5. Installation and Usage

### 5.1 Project Structure

```
MHH/
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
├── README.md                  # This file
└── test_trace.py             # Additional testing
```

### 5.2 Installation Steps

1. **Clone or Download the Project:**
   ```bash
   git clone <repository-url>
   cd MHH
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r src/requirements.txt
   ```

   Dependencies include:
   - `dd>=0.2.0` - Binary Decision Diagram library
   - `pulp>=2.7` - Linear programming solver
   - `lxml>=4.9` - XML parsing
   - `psutil>=5.9` - System resource monitoring

3. **Verify Installation:**
   ```bash
   python -c "import dd, pulp, lxml, psutil; print('All dependencies installed!')"
   ```

### 5.3 Running the Analysis

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

### 5.4 Creating Custom Test Cases

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

### 5.5 Troubleshooting

**Issue 1: Import Errors**
```
ModuleNotFoundError: No module named 'dd'
```
**Solution:** Install dependencies: `pip install -r src/requirements.txt`

**Issue 2: PNML Parsing Errors**
```
ValueError: No <net> found
```
**Solution:** Ensure PNML file has correct namespace and structure (see Section 5.4)

**Issue 3: ILP Solver Not Found**
```
PulpSolverError: PuLP: cannot execute glpsolver.exe
```
**Solution:** PuLP uses CBC solver by default (included). If issues persist, install GLPK: `pip install glpk`

**Issue 4: Memory Errors (Large Models)**
**Solution:** 
- Increase Python memory limit
- Use 64-bit Python
- Reduce model size or use BDD-only analysis

---

## 6. References

### Academic Literature

1. **Petri Nets:**
   - Murata, T. (1989). "Petri nets: Properties, analysis and applications." *Proceedings of the IEEE*, 77(4), 541-580.
   - Peterson, J. L. (1981). *Petri Net Theory and the Modeling of Systems*. Prentice Hall.

2. **Binary Decision Diagrams:**
   - Bryant, R. E. (1986). "Graph-based algorithms for boolean function manipulation." *IEEE Transactions on Computers*, C-35(8), 677-691.
   - Burch, J. R., et al. (1990). "Symbolic model checking: 10²⁰ states and beyond." *LICS*, 428-439.

3. **Model Checking:**
   - Clarke, E. M., Grumberg, O., & Peled, D. A. (1999). *Model Checking*. MIT Press.
   - Baier, C., & Katoen, J. P. (2008). *Principles of Model Checking*. MIT Press.

4. **ILP in Verification:**
   - Esparza, J., & Melzer, S. (2000). "Verification of safety properties using integer programming: Beyond the state equation." *Formal Methods in System Design*, 16(2), 159-189.

### Tools and Libraries

- **PNML Standard:** https://www.pnml.org/
- **dd (BDD library):** https://github.com/tulip-control/dd
- **PuLP (ILP library):** https://coin-or.github.io/pulp/
- **Model Checking Contest:** https://mcc.lip6.fr/ (Petri net benchmarks)

### Related Tools

- **LoLA:** Low-level Petri net analyzer
- **ITS-Tools:** Integrated Tool Set for model checking
- **TAPAAL:** Timed-Arc Petri Net Analyzer
- **GreatSPN:** Graphical Editor and Analyzer for Petri Nets

---

## Appendix: Output Interpretation

### Explicit Reachability Output
```
[Explicit] Reachable: 2 | Time: 0.000s | Mem: 43.8MB
```
- **Reachable:** Number of distinct states explored
- **Time:** Wall-clock time in seconds
- **Mem:** Peak memory usage (includes Python runtime)

### Symbolic Reachability Output
```
[BDD] Reachable markings: 2
[BDD] Iterations: 2 | Time: 0.000s | Mem: 44.3MB
```
- **Reachable markings:** States counted via BDD enumeration
- **Iterations:** Number of fixpoint iterations until convergence
- **Time/Mem:** Same as explicit

### Deadlock Detection Output
```
[ILP] DEADLOCK FOUND: {'a': 1, 'b': 1, 'r1': 0, 'r2': 0}
```
- **DEADLOCK FOUND:** Marking where no transition is enabled
- If no deadlock exists: `[ILP] No deadlock found.`

### Optimization Output
```
[OPT] Optimal marking: {'a': 1, 'b': 1, 'r1': 1, 'r2': 1} | Value: 4
```
- **Optimal marking:** Reachable marking maximizing the objective
- **Value:** Objective function value (Σ cₚ · mₚ)

---

## Conclusion

This project successfully implements a comprehensive Petri net analysis framework demonstrating both classical (explicit) and modern (symbolic, hybrid) verification techniques. The combination of BFS, BDD, and ILP showcases different trade-offs in state-space exploration and demonstrates how hybrid methods can leverage the strengths of multiple approaches. The implementation provides a solid foundation for further research in formal verification and model checking.

---

**Course:** CO2011 - Model Checking and Hardware Verification  
**Institution:** [Your University]  
**Semester:** Fall 2025

*For questions or contributions, please contact the author.*
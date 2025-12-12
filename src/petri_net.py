# src/petri_net.py
from typing import Dict, Set, List
from collections import defaultdict

class PetriNet:
    def __init__(self):
        self.places: Dict[str, str] = {}
        self.transitions: Dict[str, str] = {}
        self.pre: Dict[str, Set[str]] = defaultdict(set)
        self.post: Dict[str, Set[str]] = defaultdict(set)
        self.initial_marking: Dict[str, int] = {}
        self.place_order: List[str] = []

    def add_place(self, pid: str, name: str, tokens: int = 0):
        self.places[pid] = name
        self.initial_marking[pid] = tokens
        if pid not in self.place_order:
            self.place_order.append(pid)

    def add_transition(self, tid: str, name: str):
        self.transitions[tid] = name

    def add_arc(self, source: str, target: str):
        if source in self.places and target in self.transitions:
            self.pre[target].add(source)
        elif source in self.transitions and target in self.places:
            self.post[source].add(target)

    def is_enabled(self, t: str, marking: Dict[str, int]) -> bool:
        return all(marking.get(p, 0) >= 1 for p in self.pre[t])

    def fire(self, t: str, marking: Dict[str, int]) -> Dict[str, int]:
        if not self.is_enabled(t, marking):
            return marking
        new_m = marking.copy()
        for p in self.pre[t]:
            new_m[p] -= 1
        for p in self.post[t]:
            new_m[p] = new_m.get(p, 0) + 1
        return new_m

    def marking_to_tuple(self, marking: Dict[str, int]) -> tuple:
        return tuple(marking.get(p, 0) for p in self.place_order)

    def tuple_to_marking(self, state):
        """
        Fix: Skip primed 'x0_', convert True → 1, False → 0
        """
        if isinstance(state, dict):
            marking = {}
            for key, val in state.items():
                if '_' in key: continue  # skip primed x0_
                if isinstance(key, str) and key.startswith('x'):
                    i = int(key[1:])
                else:
                    i = key
                p = self.place_order[i]
                marking[p] = 1 if val else 0
            return marking
        else:
            return {self.place_order[i]: state[i] for i in range(len(self.place_order))}
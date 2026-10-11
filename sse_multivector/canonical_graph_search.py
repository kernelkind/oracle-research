"""Select local-versus-canonical comparisons by traversing a fixed graph.

Comparison labels are trusted. Positive containment propagates through existing
edges. Traversal prunes neither and holds uncertain. No ranking, inference
transport, prompt changes or fabricated model answers belong in this selector.
"""
from graphlib import CycleError, TopologicalSorter


RELATIONS = frozenset(('equivalent', 'canonical_contains_local',
                       'local_contains_canonical', 'neither', 'uncertain'))


class GraphSearch:
    """Expose the next comparisons; accept their unchanged relationship labels.

    Call candidates(), obtain or reuse native answers, then record(labels).
    Repeat until candidates() is empty. Partial batches are supported. Native
    callers keep graph/meaning/receipt bindings and placement checks themselves.
    """

    def __init__(self, nodes):
        self._held = False
        self.parents = {}
        for node in nodes:
            identifier, parents = node['id'], node['parents']
            if (not isinstance(identifier, str) or not identifier
                    or identifier in self.parents or not isinstance(parents, list)
                    or any(not isinstance(p, str) for p in parents)
                    or len(parents) != len(set(parents))):
                raise ValueError('canonical IDs and parents must be unique')
            self.parents[identifier] = tuple(parents)
        if any(p not in self.parents for ps in self.parents.values() for p in ps):
            raise ValueError('unknown canonical parent')
        try:
            self.order = tuple(TopologicalSorter(self.parents).static_order())
        except CycleError as error:
            raise ValueError('canonical cycle') from error
        self.children = {k: [] for k in self.parents}
        for identifier, parents in self.parents.items():
            for parent in parents:
                self.children[parent].append(identifier)
        self._queue = dict.fromkeys(k for k, ps in self.parents.items() if not ps)
        self._visited = set()
        self._selected = set()
        self._answers = {}
        self._inferred = {}

    def _expand(self, identifier):
        for child in self.children[identifier]:
            if child not in self._visited:
                self._queue.setdefault(child, None)

    def _infer(self, identifier, relation, branches):
        stack = list(branches[identifier])
        while stack:
            other = stack.pop()
            if self._inferred.get(other) == relation:
                continue
            self._inferred[other] = relation
            stack.extend(branches[other])

    def candidates(self):
        """Return each currently reachable node once, without a cap."""
        if self._held:
            return []
        while True:
            skipped = [k for k in self._queue if k in self._inferred]
            if not skipped:
                break
            for identifier in skipped:
                del self._queue[identifier]
                self._visited.add(identifier)
                if self._inferred[identifier] == 'canonical_contains_local':
                    self._expand(identifier)
        blocked = {}
        for identifier in self.order:
            blocked[identifier] = any(p in self._queue or blocked[p]
                                      for p in self.parents[identifier])
        ready = [k for k in self.parents if k in self._queue and not blocked[k]]
        self._selected.update(ready)
        return ready

    def record(self, labels):
        """Consume a batch from the exposed frontier, never a speculative pair."""
        self.candidates()
        if (not isinstance(labels, dict) or set(labels) - self._selected
                or set(labels) & self._answers.keys()
                or any(relation not in RELATIONS for relation in labels.values())):
            raise ValueError('answers must supply valid labels for selected, unanswered candidates')
        for identifier, relation in labels.items():
            self._queue.pop(identifier, None)
            self._visited.add(identifier)
            self._answers[identifier] = relation
            if relation in ('canonical_contains_local', 'equivalent'):
                self._infer(identifier, 'canonical_contains_local', self.parents)
            if relation in ('local_contains_canonical', 'equivalent'):
                self._infer(identifier, 'local_contains_canonical', self.children)
            elif relation == 'canonical_contains_local':
                self._expand(identifier)
            elif relation == 'uncertain':
                self._held = True

    def result(self):
        pending = self.candidates()
        result = dict(queried=list(self._answers), pending=pending, complete=not pending,
                    inferred={k: v for k, v in self._inferred.items()
                              if k not in self._answers})
        result['held'] = self._held
        return result

"""Select local-versus-canonical comparisons by traversing a fixed graph.

Comparison labels are trusted. Positive containment propagates through existing
edges; neither and uncertain leave children available. No ranking, inference
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

    def __init__(self, nodes, *, eligible=None, required=()):
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
            tuple(TopologicalSorter(self.parents).static_order())
        except CycleError as error:
            raise ValueError('canonical cycle') from error
        self.eligible = set(self.parents if eligible is None else eligible)
        self.required = set(required)
        if self.eligible - self.parents.keys() or self.required - self.eligible:
            raise ValueError('eligible and required comparisons must identify canonical nodes')
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
        """Return each currently reachable eligible node once, without a cap."""
        while True:
            skipped = [k for k in self._queue if k not in self.eligible
                       or k in self._inferred and k not in self.required]
            if not skipped:
                break
            for identifier in skipped:
                del self._queue[identifier]
                self._visited.add(identifier)
                if (identifier not in self.eligible
                        or self._inferred[identifier] == 'canonical_contains_local'):
                    self._expand(identifier)
        if self._queue:
            self._selected.update(self._queue)
            return list(self._queue)
        # Preserve native requirements, such as comparing the mapped original
        # parent, even when its relationship followed from an earlier answer.
        for identifier in self.parents:
            if identifier in self.required and identifier not in self._answers:
                self._queue[identifier] = None
        self._selected.update(self._queue)
        return list(self._queue)

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
            else:
                self._expand(identifier)

    def result(self):
        pending = self.candidates()
        return dict(queried=list(self._answers), pending=pending, complete=not pending,
                    inferred={k: v for k, v in self._inferred.items()
                              if k in self.eligible and k not in self._answers})

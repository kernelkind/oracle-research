"""Add audited, forward-only SUMO class ancestors to a supplied WordNet order.

Only top-level ground facts are read from KIF. This is not a logical reasoner:
instance facts document class roles but never become subclass edges. Positive
mapping annotations are fallible candidate ancestors, not identity equivalences.
"""

from collections import defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass
import json
import re


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True)
class _Form:
    items: tuple
    start: int
    end: int
    line: int


_TOKEN = re.compile(r'(?P<space>\s+)|(?P<comment>;[^\n]*)|(?P<open>\()|'
                    r'(?P<close>\))|(?P<string>"(?:\\.|[^"\\])*")|'
                    r"(?P<quote>['`])|(?P<atom>[^\s();\"'`]+)", re.DOTALL)


def _forms(text, source):
    tokens = []
    offset, line, column = 0, 1, 1
    while offset < len(text):
        match = _TOKEN.match(text, offset)
        if match is None:
            raise ValueError(f'{source}:{line}:{column}: unterminated string or invalid token')
        value, kind = match.group(), match.lastgroup
        if kind not in {'space', 'comment'}:
            tokens.append(_Token(kind, value, offset, match.end(), line, column))
        line += value.count('\n')
        column = len(value.rsplit('\n', 1)[-1]) + 1 if '\n' in value else column + len(value)
        offset = match.end()
    index = 0

    def read():
        nonlocal index
        token = tokens[index]
        index += 1
        if token.kind == 'close':
            raise ValueError(f'{source}:{token.line}:{token.column}: unmatched closing parenthesis')
        if token.kind == 'quote':
            if index == len(tokens):
                raise ValueError(f'{source}:{token.line}:{token.column}: missing quoted expression')
            item = read()
            return _Form((token, item), token.start, item.end, token.line)
        if token.kind != 'open':
            return token
        items = []
        while index < len(tokens) and tokens[index].kind != 'close':
            items.append(read())
        if index == len(tokens):
            raise ValueError(f'{source}:{token.line}:{token.column}: unmatched opening parenthesis')
        end = tokens[index].end
        index += 1
        return _Form(tuple(items), token.start, end, token.line)

    while index < len(tokens):
        result = read()
        if not isinstance(result, _Form):
            raise ValueError(f'{source}:{result.line}:{result.column}: expected top-level expression')
        yield result


def _ground_symbol(value):
    return isinstance(value, _Token) and value.kind == 'atom' and not value.value.startswith(('?', '@'))


def parse_ontology(files):
    """Read explicit class roles, subclass edges, instance facts and definitions.

    Every fact and definition retains its source file, opening line and exact
    source expression. Repeated facts keep each location; parent edges deduplicate.
    """
    classes, parents, definitions, facts = set(), defaultdict(set), defaultdict(list), []
    for source, text in sorted(files.items()):
        for form in _forms(text, source):
            items = form.items
            if not items or not _ground_symbol(items[0]):
                continue
            predicate = items[0].value
            location = {'file': source, 'line': form.line, 'raw': text[form.start:form.end]}
            if predicate in {'subclass', 'instance'} and len(items) == 3 and all(
                    _ground_symbol(item) for item in items[1:]):
                subject, target = (item.value for item in items[1:])
                facts.append({'predicate': predicate, 'subject': subject, 'object': target, **location})
                classes.add(target)
                if predicate == 'subclass':
                    classes.add(subject)
                    parents[subject].add(target)
            elif predicate == 'documentation' and len(items) == 4 and all(
                    _ground_symbol(item) for item in items[1:3]) and isinstance(items[3], _Token) and items[3].kind == 'string':
                definition = re.sub(r'\\(.)', lambda m: {'n': '\n', 'r': '\r', 't': '\t'}.get(m[1], m[1]),
                                    items[3].value[1:-1], flags=re.DOTALL)
                definitions[items[1].value].append({'text': definition, 'language': items[2].value, **location})

    # A subject explicitly instantiated as Class, or as a subclass of Class,
    # is itself a class. Ordinary instance subjects are not promoted.
    def is_metaclass(term):
        pending, seen = [term], set()
        while pending:
            current = pending.pop()
            if current == 'Class':
                return True
            if current not in seen:
                seen.add(current)
                pending.extend(parents.get(current, ()))
        return False

    classes.update(fact['subject'] for fact in facts
                   if fact['predicate'] == 'instance' and is_metaclass(fact['object']))
    return {'classes': sorted(classes),
            'parents': {term: sorted(parents.get(term, ())) for term in sorted(classes)},
            'definitions': dict(sorted(definitions.items())), 'facts': facts}


_MAPPING = re.compile(r'&%([A-Za-z][A-Za-z0-9_-]*)([=+@:\[\]])\Z')
_RELATIONS = set('=+@:[\u005d')


def _mapping_tail(gloss):
    # Read only the terminal annotation run. Annotation-looking words embedded
    # earlier in ordinary gloss text are not mappings. Keep malformed spacing in
    # that run so it invalidates the whole row instead of salvaging a substring.
    tokens = gloss.split()
    index = len(tokens)
    while index:
        last = tokens[index - 1]
        if last.startswith('&%'):
            index -= 1
        elif index >= 2 and (tokens[index - 2] == '&%' or
                            (last in _RELATIONS and tokens[index - 2].startswith('&%'))):
            index -= 2
        elif index >= 3 and last in _RELATIONS and tokens[index - 3] == '&%':
            index -= 3
        else:
            break
    return tokens[index:]


def parse_mappings(text, pos, source):
    """Index exact WordNet offsets, preserving typed conjunction annotations.

    Malformed terminal annotations produce an audited row with no mappings.
    Structural offset/POS errors raise, since they invalidate lookup identity.
    """
    if pos not in {'n', 'v', 'a', 's', 'r'}:
        raise ValueError(f'unsupported WordNet POS {pos!r}')
    rows = {}
    for line_number, raw in enumerate(text.splitlines(), 1):
        if not re.match(r'^\s*\d{8}(?:\s|$)', raw):
            continue
        prefix, separator, gloss = raw.partition('|')
        fields = prefix.split()
        if not separator or len(fields) < 3:
            raise ValueError(f'{source}:{line_number}: invalid WordNet row prefix')
        actual_pos = fields[2]
        if actual_pos != pos and not (pos == 'a' and actual_pos == 's'):
            raise ValueError(f'{source}:{line_number}: WordNet POS {actual_pos!r} differs from {pos!r}')
        row = {'offset': fields[0], 'pos': actual_pos, 'mappings': [],
               'file': source, 'line': line_number, 'raw': raw}
        tokens = _mapping_tail(gloss)
        parsed = [_MAPPING.fullmatch(token) for token in tokens]
        if any(match is None for match in parsed):
            row['error'] = 'invalid_terminal_annotations'
        else:
            row['mappings'] = [{'term': match[1], 'relation': match[2]} for match in parsed]
        key = f'{actual_pos}:{fields[0]}'
        if key not in rows:
            rows[key] = row
        else:
            previous = rows[key]
            if previous['raw'].strip() != row['raw'].strip():
                previous['mappings'] = []
                previous['error'] = 'conflicting_duplicate_offset'
            previous.setdefault('duplicates', []).append(row)
    return rows


def _wordnet_path(lexicon, source, target):
    if source == target:
        return []
    saved = lexicon[source].get('paths', {}).get(target)
    if saved:
        if saved[0] != source or saved[-1] != target:
            raise ValueError(f'invalid saved WordNet path from {source} to {target}')
        pairs = list(zip(saved, saved[1:]))
        if any(end not in lexicon.get(start, {}).get('hypernyms', ()) for start, end in pairs):
            raise ValueError(f'unsupported saved WordNet hypernym path from {source} to {target}')
        return [{'type': 'wordnet_hypernym', 'source': start, 'target': end,
                 'field': 'hypernyms'} for start, end in pairs]
    pending, seen = deque([(source, [])]), {source}
    while pending:
        current, path = pending.popleft()
        for parent in sorted(lexicon.get(current, {}).get('hypernyms', ())):
            new_path = path + [{'type': 'wordnet_hypernym', 'source': current,
                                'target': parent, 'field': 'hypernyms'}]
            if parent == target:
                return new_path
            if parent not in seen:
                seen.add(parent)
                pending.append((parent, new_path))
    # Supplied orders without immediate-edge metadata still explicitly support
    # a transitive ancestor step; never label that step a direct hypernym.
    return [{'type': 'wordnet_ancestor', 'source': source, 'target': target, 'field': 'ancestors'}]


def augment(lexicon, mappings_by_sense, ontology, allowed_pos):
    """Preserve the supplied order, adding distinct SUMO nodes and audited paths.

    Each added ancestor has one deterministic shortest path. All admitted
    annotations remain in ``admitted`` and all ontology facts remain available
    in the supplied parsed ontology, including alternative paths and duplicates.
    """
    if not set(allowed_pos) <= {'n', 'v'}:
        raise ValueError('only noun and verb mappings may augment this order')
    if any(name.startswith('SUMO:') for name in lexicon):
        raise ValueError('input WordNet order contains reserved SUMO: identities')
    for name, entry in lexicon.items():
        if name not in entry.get('ancestors', ()):
            raise ValueError(f'WordNet ancestors of {name} must include itself')
        for ancestor in entry['ancestors']:
            if ancestor == name or ancestor not in lexicon:
                continue
            if name in lexicon[ancestor]['ancestors']:
                raise ValueError(f'cyclic WordNet order: {name} -> {ancestor} -> {name}')
            if not set(lexicon[ancestor]['ancestors']) <= set(entry['ancestors']):
                raise ValueError(f'incomplete WordNet ancestor closure for {name}')

    admitted, excluded, mapping_edges = [], [], defaultdict(list)
    classes = set(ontology['classes'])
    for sense, row in sorted(mappings_by_sense.items()):
        base = {'sense': sense, **deepcopy(row)}
        base.pop('mappings', None)
        if row.get('error') or not row['mappings']:
            excluded.append({**base, 'reason': row.get('error', 'unmapped')})
            continue
        for index, mapping in enumerate(row['mappings']):
            audit = {**base, **mapping, 'mapping_index': index}
            reason = None
            if sense not in lexicon or lexicon[sense].get('known') is False:
                reason = 'unknown_wordnet_sense'
            elif row['pos'] not in allowed_pos:
                reason = 'excluded_pos'
            elif mapping['relation'] not in {'=', '+'}:
                reason = 'unsupported_mapping_relation'
            elif mapping['term'] not in classes:
                reason = 'target_not_declared_class'
            if reason:
                excluded.append({**audit, 'reason': reason})
                continue
            admitted.append(audit)
            mapping_edges[sense].append({'type': 'mapping', 'source': sense,
                                         'target': 'SUMO:' + mapping['term'], **audit})

    edge_facts = defaultdict(list)
    for fact in ontology['facts']:
        if fact['predicate'] == 'subclass':
            edge_facts[fact['subject'], fact['object']].append(fact)
    for facts in edge_facts.values():
        facts.sort(key=lambda fact: (fact['file'], fact['line'], fact['raw']))

    def edge(source, target):
        facts = edge_facts.get((source, target))
        if not facts:
            raise ValueError(f'missing ground subclass provenance: {source} -> {target}')
        return {'type': 'subclass', 'source': 'SUMO:' + source,
                'target': 'SUMO:' + target, **deepcopy(facts[0])}

    # Validate the entire reachable subclass graph, not just whichever edges a
    # shortest-path search happens to use. Unreachable ontology cycles add no
    # ancestors to this intervention and remain in the retained resource facts.
    completed, active = set(), []

    def validate(term):
        if term in active:
            cycle = active[active.index(term):] + [term]
            locations = [f"{edge(a, b)['file']}:{edge(a, b)['line']}" for a, b in zip(cycle, cycle[1:])]
            raise ValueError('cyclic SUMO order: ' + ' -> '.join('SUMO:' + item for item in cycle)
                             + ' (' + ', '.join(locations) + ')')
        if term in completed:
            return
        active.append(term)
        for parent in sorted(ontology['parents'].get(term, ())):
            edge(term, parent)
            validate(parent)
        active.pop()
        completed.add(term)

    for term in sorted({item['term'] for item in admitted}):
        validate(term)

    closure = {}
    for term in sorted(completed):
        paths, pending = {term: []}, deque([term])
        while pending:
            current = pending.popleft()
            for parent in sorted(ontology['parents'].get(current, ())):
                if parent not in paths:
                    paths[parent] = paths[current] + [edge(current, parent)]
                    pending.append(parent)
        closure[term] = paths

    senses = deepcopy(lexicon)
    for name in sorted(lexicon):
        paths = {}
        for ancestor in sorted(set(lexicon[name]['ancestors']) & mapping_edges.keys()):
            prefix = _wordnet_path(lexicon, name, ancestor)
            for mapping in mapping_edges[ancestor]:
                for term, suffix in closure[mapping['term']].items():
                    target, path = 'SUMO:' + term, prefix + [mapping] + suffix
                    rank = lambda value: (len(value), json.dumps(value, sort_keys=True))
                    if target not in paths or rank(path) < rank(paths[target]):
                        paths[target] = path
        if paths:
            senses[name]['ancestors'] = senses[name]['ancestors'] + sorted(paths)
            senses[name]['ontology_paths'] = dict(sorted(paths.items()))
    for term, paths in sorted(closure.items()):
        definitions = deepcopy(ontology['definitions'].get(term, []))
        senses['SUMO:' + term] = {
            'ancestors': sorted('SUMO:' + target for target in paths),
            'hypernyms': ['SUMO:' + parent for parent in sorted(ontology['parents'].get(term, ()))],
            'definition': definitions[0]['text'] if definitions else '',
            'definitions': definitions, 'known': True,
            'ontology_paths': {'SUMO:' + target: path for target, path in sorted(paths.items())},
        }
    return {'senses': senses, 'admitted': admitted, 'excluded': excluded}

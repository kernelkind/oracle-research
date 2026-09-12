"""Fixed English Snowball word-form control over frozen source candidates.

Stemming affects contiguous token matching only. Candidate IDs, labels and raw
features remain unchanged; no learned model, category selection or propagation.
"""

import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
import platform

import nltk
from nltk.stem.snowball import EnglishStemmer

import category_path_compatibility as compatibility


def compare_memberships(patterns, candidates):
    """Compare frozen literal memberships with contiguous stem-sequence matches."""
    if nltk.__version__ != '3.9.2':
        raise ValueError('the fixed control requires NLTK 3.9.2')
    # Reproduce only to validate the saved family; never replace or select from it.
    anchors = [c['label'] for c in candidates if c['family'] == 'unigram']
    expected = compatibility.prepare_candidates(patterns, anchors)
    if expected['candidates'] != candidates:
        raise ValueError('frozen candidates differ from their source-derived literal records')
    stemmer = EnglishStemmer(ignore_stopwords=False)
    tokens, inputs = patterns['tokens'], patterns['inputs']
    spans = patterns['casefolded_character_spans']
    stemmed = [[stemmer.stem(token) for token in row] for row in tokens]
    memberships = []
    for original in candidates:
        target = [stemmer.stem(token) for token in original['tokens']]
        width = len(target)
        positions, characters, matches = [], [], []
        for row, words in enumerate(stemmed):
            starts = [i for i in range(len(words) - width + 1) if words[i:i + width] == target]
            if not starts:
                continue
            indices = [list(range(i, i + width)) for i in starts]
            occurrences = [[spans[row][i][0], spans[row][i + width - 1][1]] for i in starts]
            positions.append([row, indices])
            characters.append([row, occurrences])
            for i, indices_at_i, (start, end) in zip(starts, indices, occurrences):
                matches.append(dict(row=row, note=inputs[row]['note'], token_positions=indices_at_i,
                                    casefolded_character_span=[start, end],
                                    casefolded_text=inputs[row]['subject'].casefold()[start:end],
                                    raw_tokens=tokens[row][i:i + width],
                                    stemmed_tokens=words[i:i + width]))
        rows = [row for row, _ in positions]
        notes = sorted({inputs[row]['note'] for row in rows})
        candidate = copy.deepcopy(original)
        candidate.update(stemmed_tokens=target, positions=positions,
                         casefolded_character_occurrences=characters, matches=matches,
                         rows=rows, notes=notes,
                         added_rows=sorted(set(rows) - set(original['rows'])),
                         removed_rows=sorted(set(original['rows']) - set(rows)),
                         added_notes=sorted(set(notes) - set(original['notes'])),
                         removed_notes=sorted(set(original['notes']) - set(notes)))
        memberships.append(candidate)
    literal = compatibility._membership_summary(copy.deepcopy(candidates))
    normalized = compatibility._membership_summary(memberships)
    changes = {}
    for rule, relation in normalized['relations'].items():
        changes[rule] = {}
        for field in ('all_edges', 'immediate_edges'):
            old = {tuple(e) for e in literal['relations'][rule][field]}
            new = {tuple(e) for e in relation[field]}
            changes[rule][field] = dict(added=[list(e) for e in sorted(new - old)],
                                        removed=[list(e) for e in sorted(old - new)])
    return dict(literal=literal, stemmed=normalized, edge_changes=changes)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('patterns', 'prepared', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError('output exists; preserve frozen results')
    raw = args.patterns.read_bytes()
    input_raw = (args.prepared / 'inputs.json').read_bytes()
    candidate_raw = (args.prepared / 'candidates.json').read_bytes()
    prepared_raw = (args.prepared / 'config.json').read_bytes()
    prepared_config = json.loads(prepared_raw)
    if (compatibility._sha(raw) != prepared_config['patterns_source']['sha256']
            or compatibility._sha(input_raw) != prepared_config['inputs_sha256']
            or compatibility._sha(candidate_raw) != prepared_config['candidates_sha256']):
        raise ValueError('frozen source, input or candidate hash mismatch')
    for name, digest in prepared_config['code_sha256'].items():
        if compatibility._sha((args.prepared / 'source' / name).read_bytes()) != digest:
            raise ValueError('prepared source snapshot hash mismatch')
    patterns, candidates = json.loads(raw), json.loads(candidate_raw)
    if patterns['inputs'] != json.loads(input_raw):
        raise ValueError('prepared inputs differ from CAP04 source records')
    result = compare_memberships(patterns, candidates)
    snapshots = {name: Path(__file__).with_name(name).read_bytes() for name in
                 ('category_morphology_control.py', 'category_path_compatibility.py',
                  'mask_description_hierarchy.py', 'select_mask_distinctions.py',
                  'select_note_categories.py')}
    nltk_root = Path(nltk.__file__).parent
    nltk_sources = {name: (nltk_root / name).read_bytes() for name in
                    ('__init__.py', 'stem/__init__.py', 'stem/snowball.py',
                     'stem/api.py', 'stem/util.py', 'stem/porter.py')}
    distribution = importlib.metadata.distribution('nltk')
    package_metadata = {name: distribution.read_text(name) for name in ('METADATA', 'RECORD')}
    if any(value is None for value in package_metadata.values()):
        raise ValueError('installed NLTK package metadata and RECORD required for provenance')
    config = dict(normalizer='nltk.stem.snowball.EnglishStemmer', ignore_stopwords=False,
                  packages=dict(nltk=nltk.__version__), python=platform.python_version(),
                  patterns_source=compatibility._source(args.patterns, raw),
                  prepared_source=compatibility._source(args.prepared / 'config.json', prepared_raw),
                  inputs_sha256=compatibility._sha(input_raw),
                  candidates_sha256=compatibility._sha(candidate_raw),
                  code_sha256={name: compatibility._sha(value) for name, value in snapshots.items()},
                  nltk_source_sha256={name: compatibility._sha(value) for name, value in nltk_sources.items()},
                  nltk_package_metadata_sha256={name: compatibility._sha(value.encode())
                                                for name, value in package_metadata.items()},
                  input_count=len(patterns['inputs']), candidate_count=len(candidates),
                  note_count=len({r['note'] for r in patterns['inputs']}),
                  labels=[c['label'] for c in candidates],
                  matching_rule='contiguous_stemmed_CAP04_tokens_within_one_subject',
                  note_membership_rule='any_matching_subject',
                  limitations=['normalization affects membership matching, not relation features or labels',
                               'positions index CAP04 tokens and casefolded subject characters',
                               'stemmed matches are not necessarily literal label occurrences',
                               'word-form normalization does not establish word-sense identity',
                               'all candidates remain, including empty and equal-note-set candidates',
                               'no semantic judgments, learned model, selection or membership propagation'])
    artifacts = {'inputs.json': input_raw, 'candidates.json': candidate_raw,
                 'prepared-config.json': prepared_raw, 'result.json': compatibility._json_bytes(result),
                 'config.json': compatibility._json_bytes(config)}
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in artifacts.items():
        with (args.output / name).open('xb') as stream:
            stream.write(value)
    for name, value in snapshots.items():
        destination = args.output / 'source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(value)
    for name, value in {**nltk_sources, **{name: text.encode() for name, text in package_metadata.items()}}.items():
        destination = args.output / 'source' / 'nltk' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(value)
    print(json.dumps(dict(inputs=config['input_count'], notes=config['note_count'],
                          candidates=config['candidate_count'])))


if __name__ == '__main__':
    main()

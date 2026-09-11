"""Diagnostic category utility; no category selection or membership changes.

Implements P(c) * sum_y(P(y|c)^2 - P(y)^2), with binary masked-word
attributes and explicit source-note balancing. Not a semantic quality score.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from select_mask_distinctions import describe_categories, mask_words


def note_weights(evidence):
    notes = [e['aliases'][0]['note_short_id'] for e in evidence]
    counts = Counter(notes)
    return [1 / len(counts) / counts[n] for n in notes]


def utility_scores(features, weights, groups):
    if len(features) != len(weights) or not math.isclose(sum(weights), 1) or any(w <= 0 for w in weights):
        raise ValueError('each object needs positive weight and total weight must be one')
    marginal = Counter()
    for words, w in zip(features, weights):
        for word in words:
            marginal[word] += w
    baseline = sum(p*p for p in marginal.values())
    results = {}
    for i, rows in groups.items():
        if not rows or len(rows) != len(set(rows)) or any(r < 0 or r >= len(features) for r in rows):
            raise ValueError('group must contain valid distinct objects')
        mass = sum(weights[r] for r in rows)
        conditional = Counter()
        for row in rows:
            for word in features[row]:
                conditional[word] += weights[row] / mass
        results[i] = dict(utility=mass*(sum(p*p for p in conditional.values())-baseline),
                          probability_mass=mass)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('categories', type=Path)
    parser.add_argument('--hierarchy', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve previous evidence')
    sources, data = {}, {}
    for key in ('categories', 'hierarchy', 'evidence'):
        path = getattr(args, key)
        raw = path.read_bytes()
        sources[key] = dict(path=str(path.resolve()), sha256=hashlib.sha256(raw).hexdigest())
        data[key] = json.loads(raw)
    profiles = describe_categories(**data)
    evidence = data['evidence']
    features = [mask_words(e['aliases'][0]['fragments']) for e in evidence]
    weights = note_weights(evidence)
    groups = {i: d['rows'] for i, d in profiles.items()}
    scores = utility_scores(features, weights, groups)
    dependencies = {}
    for name in ('category_utility.py', 'select_mask_distinctions.py', 'select_note_categories.py'):
        path = Path(__file__).with_name(name)
        dependencies[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = dict(sources=sources, code_sha256=dependencies,
                  source='https://www.ijcai.org/Proceedings/13/Papers/186.pdf',
                  formula='P(c) * sum_y(P(y|c)^2 - P(y)^2)',
                  attributes='binary casefolded words in each canonical mask; no stopwords',
                  weighting='equal total mass per source note, uniform among its canonical masks',
                  purpose='diagnostic only; no cutoff or hierarchy selection',
                  feature_count=len(set().union(*features)), weights=weights, scores=scores,
                  ranking=sorted(scores, key=lambda i: (-scores[i]['utility'], i)))
    with args.output.open('x') as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
        file.write('\n')
    print(json.dumps(dict(categories=len(scores), attributes=result['feature_count'],
                          top_five=result['ranking'][:5])))


if __name__ == '__main__':
    main()

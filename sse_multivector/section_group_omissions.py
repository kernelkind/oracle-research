"""Audit a fixed groups-only eligibility rule; never fit or change a hierarchy.

Consume a frozen whole-corpus section panel, validate its original grouping and
reciprocal pairs, then retain only units with two or more original entries.
Exact titles are inspection aids, not semantic equivalence or accuracy labels.
"""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import re

from . import section_count_panel as panel


def audit(specification, output):
    specification, output = Path(specification).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Audit output already exists; preserve saved evidence')
    spec = panel._read(specification)
    reports, identifiers = {}, set()
    for selection in spec['cases']:
        identifier = selection['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', identifier) or identifier in identifiers:
            raise ValueError('Unique safe corpus IDs required')
        identifiers.add(identifier)
        path = selection['panel']
        panel._check_files({path: selection['panel_sha256']})
        producer = panel._read(path)
        panel._check_files(producer['code_files'])
        cfg = next(c for c in producer['cases'] if c['id'] == selection['case'])
        source = producer['spec']['sources'][cfg['source']]
        vectors, notes, entries = panel._load_source(source)
        usable_notes = set(notes.tolist())
        if (cfg['indices'] != list(range(len(entries)))
                or cfg['entry_ids'] != [e['id'] for e in entries]
                or cfg['note_ids'] != sorted(usable_notes)
                or not cfg.get('preserve_groups') or not cfg.get('reciprocal_nearest')):
            raise ValueError('Whole-corpus native/reciprocal grouping panel required')
        corpus_path = selection['corpus']
        corpus_sha = selection.get('corpus_sha256', source['files'].get(corpus_path))
        if corpus_sha is None:
            raise ValueError('Frozen original corpus required')
        panel._check_files({corpus_path: corpus_sha})
        corpus = panel._read(corpus_path)['notes']
        if (len({n['note_id'] for n in corpus}) != len(corpus)
                or not usable_notes <= {n['note_id'] for n in corpus}
                or any(n['origin']['prompt_version'] != 'ASv6.100' for n in corpus)):
            raise ValueError('Unique current ASv6.100 corpus notes required')
        membership, grouping_files = None, {}
        if 'grouping' in cfg:
            membership, grouping_files = panel._saved_grouping(
                cfg['grouping'], vectors, notes, entries,
                'meaning' if source.get('vector_view', 'vectors') == 'vectors'
                else source['vector_view'])
        initial, keys = [], {}
        for entry in entries:
            group = membership.get(entry['id']) if membership is not None else entry.get('source_group')
            key = ('entry', entry['id']) if group is None else ('group', group)
            initial.append(keys.setdefault(key, len(keys)))
        groups, pairs, _ = panel._reciprocal_groups(vectors, initial)
        if pairs != cfg['reciprocal_pairs']:
            raise ValueError('Recomputed reciprocal pairs differ from frozen producer')
        sizes = Counter(groups)
        kept = [sizes[g] >= 2 for g in groups]
        kept_by_note, omitted_by_note, members = defaultdict(list), defaultdict(list), defaultdict(list)
        group_notes = defaultdict(set)
        for entry, group, retained in zip(entries, groups, kept):
            (kept_by_note if retained else omitted_by_note)[entry['note_id']].append(entry)
            if retained:
                members[group].append(entry['id'])
                group_notes[group].add(entry['note_id'])
        retained_titles = {e['title'] for e, retain in zip(entries, kept) if retain}
        lost_titles = defaultdict(list)
        for entry, retain in zip(entries, kept):
            if not retain and entry['title'] not in retained_titles:
                lost_titles[entry['title']].append(entry['id'])
        report = dict(
            status='Offline eligibility audit; no hierarchy or admission policy adopted',
            files={path: selection['panel_sha256'], corpus_path: corpus_sha,
                   **source['files'], **grouping_files},
            rule='Retain native/reciprocal units with at least two original entries; no one-way links',
            counts=dict(corpus_notes=len(corpus), usable_notes=len(usable_notes),
                        unavailable_notes=len(corpus) - len(usable_notes),
                        retained_notes=len(kept_by_note),
                        omitted_usable_notes=len(usable_notes - set(kept_by_note)),
                        retained_notes_with_omissions=len(set(kept_by_note) & set(omitted_by_note)),
                        entries=len(entries), retained_entries=sum(kept), omitted_entries=len(entries)-sum(kept),
                        retained_groups=len(members), wholly_omitted_title_strings=len(lost_titles),
                        retained_single_note_groups=sum(len(v) == 1 for v in group_notes.values())),
            retained_groups=[dict(group=g, entry_ids=ids) for g, ids in members.items()],
            wholly_omitted_titles=dict(sorted(lost_titles.items())),
            notes=[dict(note_id=n['note_id'], text=n['text'],
                        retained=kept_by_note.get(n['note_id'], []),
                        omitted=omitted_by_note.get(n['note_id'], []),
                        usable=n['note_id'] in usable_notes) for n in corpus])
        reports[identifier] = report
        del vectors
    output.mkdir(parents=True)
    for identifier, report in reports.items():
        panel._write(output / (identifier + '.json'), report)
    summary = dict(specification=str(specification), specification_sha256=panel._sha(specification),
                   code_files={str(Path(__file__).resolve()): panel._sha(__file__)},
                   corpora={key: value['counts'] for key, value in reports.items()})
    panel._write(output / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('specification')
    parser.add_argument('output')
    args = parser.parse_args()
    print(audit(args.specification, args.output))


if __name__ == '__main__':
    main()

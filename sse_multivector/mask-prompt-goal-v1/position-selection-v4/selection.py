"""Experimental word-ID mask interface; no occurrence search or boundary repair."""
import json
import re


def words(source):
    if '⟦' in source or '⟧' in source:
        raise ValueError('source already contains reserved marking characters')
    return list(re.finditer(r'\S+', source))


def index_post(source):
    result, cursor = [], 0
    for number, word in enumerate(words(source), 1):
        result.extend((source[cursor:word.start()], f'[{number}]', word.group()))
        cursor = word.end()
    result.append(source[cursor:])
    return ''.join(result)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def marked_bounds(marked, word):
    if not isinstance(marked, str) or marked.count('⟦') != 1 or marked.count('⟧') != 1:
        raise ValueError('marked word must contain one pair of brackets')
    start, end = marked.index('⟦'), marked.index('⟧') - 1
    if start >= end or marked.replace('⟦', '').replace('⟧', '') != word:
        raise ValueError('marked word must be an exact copy with a nonempty selection')
    return start, end


def decode(raw, source):
    selections = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(selections, list):
        raise ValueError('response is not a JSON array')
    tokens = words(source)
    ranges, previous_end = [], 0
    for item in selections:
        required, optional = {'start', 'end'}, {'start_marked', 'end_marked'}
        if not isinstance(item, dict) or not required <= item.keys() or item.keys() - required - optional:
            raise ValueError('expected start, end and optional boundary markings')
        first, last = item['start'], item['end']
        if type(first) is not int or type(last) is not int or not 1 <= first <= last <= len(tokens):
            raise ValueError('invalid inclusive word IDs')
        left, right = tokens[first - 1], tokens[last - 1]
        start, end = left.start(), right.end()
        if 'start_marked' in item:
            offset_start, offset_end = marked_bounds(item['start_marked'], left.group())
            start += offset_start
            if first == last:
                end = left.start() + offset_end
            elif offset_end != len(left.group()):
                raise ValueError('multiword fragment must reach the end of its first word')
        if 'end_marked' in item:
            if first == last:
                raise ValueError('single-word selections use start_marked only')
            offset_start, offset_end = marked_bounds(item['end_marked'], right.group())
            if offset_start != 0:
                raise ValueError('multiword fragment must begin at the start of its last word')
            end = right.start() + offset_end
        if not previous_end <= start < end <= len(source):
            raise ValueError('empty, overlapping, unordered or out-of-bounds selection')
        ranges.append({'start': start, 'end': end})
        previous_end = end
    return ranges

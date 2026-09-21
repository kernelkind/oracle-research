"""MPv3.28 word ranges and exact within-word text; no repair or guessed matches."""
import json
import re


def index_post(source):
    number = 0

    def label(match):
        nonlocal number
        number += 1
        return f'[{number}]' + match.group()

    return re.sub(r'\S+', label, source)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def decode(raw, source):
    response = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(response, dict) or response.keys() != {'mask'} or not isinstance(response['mask'], list):
        raise ValueError('expected a JSON object containing only a mask array')
    words = list(re.finditer(r'\S+', source))
    ranges, previous_end = [], 0
    for item in response['mask']:
        if isinstance(item, list):
            if len(item) != 2 or any(type(value) is not int for value in item):
                raise ValueError('whole-word range must contain two integer positions')
            first, last = item
            if not 1 <= first <= last <= len(words):
                raise ValueError('invalid inclusive word positions')
            start, end = words[first - 1].start(), words[last - 1].end()
        elif isinstance(item, dict) and item.keys() == {'word', 'text'}:
            position, text = item['word'], item['text']
            if type(position) is not int or not 1 <= position <= len(words):
                raise ValueError('invalid word position')
            if not isinstance(text, str) or re.fullmatch(r'\S+', text) is None:
                raise ValueError('selected text must be nonempty without whitespace')
            word = words[position - 1]
            offset = word.group().find(text)
            if offset < 0:
                raise ValueError('selected text does not occur exactly in the addressed word')
            if word.group().find(text, offset + 1) >= 0:
                raise ValueError('ambiguous selected text within the addressed word')
            start = word.start() + offset
            end = start + len(text)
        else:
            raise ValueError('expected a whole-word range or word/text selection')
        if start < previous_end:
            raise ValueError('overlapping or unordered selection')
        ranges.append({'start': start, 'end': end})
        previous_end = end
    return ranges

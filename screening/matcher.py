import csv
import difflib
import re
import unicodedata
import os
from screening.config import LIST_FILES, SCORE_SHOW, SCORE_REVIEW, SCORE_HIGH

ORG_SUFFIXES = {
    'ltd', 'limited', 'llc', 'llp', 'inc', 'corp', 'corporation',
    'pvt', 'private', 'fze', 'fzc', 'llc', 'co', 'company',
    'trading', 'enterprises', 'group', 'holdings', 'international',
    'general', 'services', 'solutions', 'industries',
}

VARIANT_FOLD = {
    'mohammed': 'muhammad', 'mohammad': 'muhammad', 'muhammed': 'muhammad',
    'mohamad': 'muhammad', 'mehmed': 'muhammad',
    'farhan': 'farhan', 'farhaan': 'farhan',
    'orion': 'orion', 'oryon': 'orion',
    'al': 'al', 'el': 'al',
}


def normalize(text):
    if not text:
        return ''
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = text.split()
    tokens = [VARIANT_FOLD.get(t, t) for t in tokens]
    tokens = [t for t in tokens if t not in ORG_SUFFIXES]
    return ' '.join(tokens)


def _score(a, b):
    if not a or not b:
        return 0
    norm_a = normalize(a)
    norm_b = normalize(b)
    if not norm_a or not norm_b:
        return 0
    full = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
    sorted_a = ' '.join(sorted(norm_a.split()))
    sorted_b = ' '.join(sorted(norm_b.split()))
    token_sort = difflib.SequenceMatcher(None, sorted_a, sorted_b).ratio()
    set_a = set(norm_a.split())
    set_b = set(norm_b.split())
    if set_a and set_b:
        intersection = ' '.join(sorted(set_a & set_b))
        union_a = ' '.join(sorted(set_a))
        union_b = ' '.join(sorted(set_b))
        ts1 = difflib.SequenceMatcher(None, intersection, union_a).ratio()
        ts2 = difflib.SequenceMatcher(None, intersection, union_b).ratio()
        token_set = max(ts1, ts2)
    else:
        token_set = 0
    return round(max(full, token_sort, token_set) * 100)


def _level(score):
    if score >= SCORE_HIGH:
        return 'high'
    if score >= SCORE_REVIEW:
        return 'review'
    if score >= SCORE_SHOW:
        return 'possible'
    return 'clear'


class Watchlist:
    def __init__(self):
        self._entries = []
        self._load()

    def _load(self):
        for path in LIST_FILES:
            path = os.path.normpath(path)
            if not os.path.exists(path):
                continue
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._entries.append(row)

    @property
    def count(self):
        return len(self._entries)

    def screen(self, name, entity_type='entity', country=None):
        matches = []
        for entry in self._entries:
            candidates = [entry.get('name', '')]
            aliases_raw = entry.get('aliases', '')
            if aliases_raw:
                candidates += [a.strip() for a in aliases_raw.split('|') if a.strip()]
            best = 0
            best_candidate = entry.get('name', '')
            for c in candidates:
                s = _score(name, c)
                if s > best:
                    best = s
                    best_candidate = c
            if best >= SCORE_SHOW:
                matches.append({
                    'uid': entry.get('uid', ''),
                    'matched_name': best_candidate,
                    'list_name': entry.get('program', entry.get('type', 'Unknown')),
                    'score': best,
                    'level': _level(best),
                    'entry': entry,
                })
        matches.sort(key=lambda m: m['score'], reverse=True)
        return matches

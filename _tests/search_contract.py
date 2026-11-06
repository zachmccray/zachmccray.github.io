"""Frozen intended destinations, independent of the generator's numeric keys."""
import json
from pathlib import Path

EXPECTED = json.loads(Path(__file__).with_name('search-destinations.json').read_text())


def identities(records):
    return sorted(({key: row[key] for key in ('doc', 'title', 'url', 'relUrl')}
                   for row in records.values()), key=lambda r: (r['doc'], r['title'], r['url']))


def expected_destinations(records):
    return identities(records) == EXPECTED

"""Publish validated V2 shadow outputs to the separate dashboard repository.

No orders, LINE messages, or V1 files are changed. Each GitHub Contents API
PUT is a separate commit; dashboard's reader rejects missing/inconsistent sets.
"""
import base64
import csv
import io
import json
import os
from pathlib import Path
from urllib import error, request

FILES = (
    'latest_early_reversal_v2.csv',
    'latest_early_events_v2.csv',
    'latest_early_summary_v2.json',
    'latest_hybrid_v2.csv',
    'latest_qualified_countries_v2.csv',
)
COUNTRIES = {'SPY','VGK','EWJ','MCHI','EWY','INDA','THD','EEM','EWT','EWZ','VNM'}


def read_csv(path, required):
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f'Invalid columns: {path.name}')
        return list(reader)


def validate(source):
    source = Path(source)
    for filename in FILES:
        if not (source / filename).is_file():
            raise ValueError(f'Missing {filename}')
    summary = json.loads((source / FILES[2]).read_text(encoding='utf-8'))
    asof = summary.get('asof')
    if not isinstance(asof, str) or len(asof) != 10:
        raise ValueError('Invalid asof')
    if summary.get('mode') != 'SHADOW_ONLY_NO_ORDERS_NO_LINE':
        raise ValueError('Unexpected V2 mode')
    if set(summary.get('country_universe', [])) != COUNTRIES or summary.get('bitcoin_proxy') != 'IBIT':
        raise ValueError('Unexpected V2 universe')
    early = read_csv(source / FILES[0], {'Group','Ticker','AsOf','Signal'})
    events = read_csv(source / FILES[1], {'Group','Ticker','Previous','Current','Event'})
    hybrid = read_csv(source / FILES[3], {'Group','Ticker','AsOf','HybridScore','HybridStatus'})
    countries = read_csv(source / FILES[4], {'Ticker','HybridScore'})
    if not early or not hybrid:
        raise ValueError('Empty scan')
    if any(r['AsOf'] != asof for r in early + hybrid):
        raise ValueError('AsOf mismatch')
    if len(countries) > 3 or any(r['Ticker'] not in COUNTRIES for r in countries):
        raise ValueError('Invalid country shortlist')
    if summary.get('event_count') != len(events):
        raise ValueError('Event count mismatch')
    if summary.get('qualified_countries') != [r['Ticker'] for r in countries]:
        raise ValueError('Country shortlist mismatch')
    if len({(r['Group'],r['Ticker']) for r in hybrid}) != len(hybrid):
        raise ValueError('Duplicate hybrid tickers')
    return asof


def publish(source, token, owner='Tawfoofoo', repo='global-allocation-dashboard', branch='main', opener=None):
    asof = validate(source)  # all files checked before any write
    if not token:
        raise ValueError('DASHBOARD_GITHUB_TOKEN missing')
    opener = opener or request.urlopen
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'global-allocation-v2-publisher',
    }
    for filename in FILES:
        url = f'https://api.github.com/repos/{owner}/{repo}/contents/data/{filename}'
        get_req = request.Request(url + f'?ref={branch}', headers=headers)
        try:
            with opener(get_req) as response:
                sha = json.load(response)['sha']
        except error.HTTPError as exc:
            if exc.code != 404:
                raise
            sha = None
        payload = {
            'message': f'Publish V2 shadow {filename} ({asof})',
            'content': base64.b64encode((Path(source) / filename).read_bytes()).decode('ascii'),
            'branch': branch,
        }
        if sha:
            payload['sha'] = sha
        put_req = request.Request(url, data=json.dumps(payload).encode(), headers={**headers, 'Content-Type':'application/json'}, method='PUT')
        with opener(put_req) as response:
            if response.status not in (200,201):
                raise RuntimeError(f'Publish failed: {filename}')
        print(f'Published data/{filename}')


if __name__ == '__main__':
    publish(Path('data'), os.environ.get('DASHBOARD_GITHUB_TOKEN', ''))

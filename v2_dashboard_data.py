"""Optional V2 shadow data reader. Never changes the V1 validation path."""
import json
from pathlib import Path
import pandas as pd

FILES = {
    'early': 'latest_early_reversal_v2.csv',
    'events': 'latest_early_events_v2.csv',
    'hybrid': 'latest_hybrid_v2.csv',
    'countries': 'latest_qualified_countries_v2.csv',
    'summary': 'latest_early_summary_v2.json',
}
REQUIRED_HYBRID = {'Group', 'Ticker', 'AsOf', 'HybridScore', 'HybridStatus'}
REQUIRED_EARLY = {'Group', 'Ticker', 'AsOf', 'Signal'}


def load_v2(data_dir: Path):
    """Return (data, issue); incomplete/stale data is never represented as current."""
    paths = {key: Path(data_dir) / name for key, name in FILES.items()}
    missing = [name for key, name in FILES.items() if not paths[key].is_file()]
    if missing:
        return None, 'V2 files not yet published: ' + ', '.join(missing)
    try:
        with paths['summary'].open(encoding='utf-8') as f:
            summary = json.load(f)
        if not isinstance(summary, dict) or not summary.get('asof'):
            raise ValueError('Missing summary asof')
        data = {'summary': summary}
        for key in ('early', 'events', 'hybrid', 'countries'):
            # Events and countries may legitimately be header-only CSVs.
            data[key] = pd.read_csv(paths[key])
        if not REQUIRED_HYBRID.issubset(data['hybrid'].columns):
            raise ValueError('Hybrid schema mismatch')
        if not REQUIRED_EARLY.issubset(data['early'].columns):
            raise ValueError('Early reversal schema mismatch')
        if not {'Ticker', 'HybridScore'}.issubset(data['countries'].columns):
            raise ValueError('Country shortlist schema mismatch')
        if len(data['countries']) > 3:
            raise ValueError('Country shortlist exceeds 3')
        if not data['hybrid']['AsOf'].astype(str).eq(str(summary['asof'])).all():
            raise ValueError('Hybrid dates differ from summary')
        if not data['early']['AsOf'].astype(str).eq(str(summary['asof'])).all():
            raise ValueError('Early dates differ from summary')
        if data['hybrid'].empty or data['early'].empty:
            raise ValueError('Empty scan universe')
        return data, None
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        return None, f'V2 data unavailable or invalid: {exc}'

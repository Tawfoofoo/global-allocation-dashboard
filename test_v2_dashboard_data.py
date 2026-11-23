import json
import pandas as pd
from v2_dashboard_data import load_v2, FILES

def fixture(tmp_path, countries=1):
    pd.DataFrame([dict(Group='Country',Ticker='INDA',AsOf='2026-11-20',Signal='Confirmed Leader')]).to_csv(tmp_path / FILES['early'],index=False)
    pd.DataFrame(columns=['Group','Ticker','Previous','Current','Event']).to_csv(tmp_path / FILES['events'],index=False)
    pd.DataFrame([dict(Group='Country',Ticker='INDA',AsOf='2026-11-20',HybridScore=100,HybridStatus='Confirmed Leader')]).to_csv(tmp_path / FILES['hybrid'],index=False)
    pd.DataFrame([dict(Ticker=f'T{i}',HybridScore=90) for i in range(countries)], columns=['Ticker','HybridScore']).to_csv(tmp_path / FILES['countries'],index=False)
    (tmp_path / FILES['summary']).write_text(json.dumps({'asof':'2026-11-20'}))

def test_missing(tmp_path):
    data, issue = load_v2(tmp_path)
    assert data is None and 'not yet published' in issue

def test_valid(tmp_path):
    fixture(tmp_path)
    data, issue = load_v2(tmp_path)
    assert issue is None and len(data['countries']) == 1

def test_empty_shortlist(tmp_path):
    fixture(tmp_path, 0)
    data, issue = load_v2(tmp_path)
    assert issue is None and data['countries'].empty

def test_too_many_countries(tmp_path):
    fixture(tmp_path, 4)
    data, issue = load_v2(tmp_path)
    assert data is None and 'exceeds' in issue

def test_mismatched_date(tmp_path):
    fixture(tmp_path)
    p = tmp_path / FILES['summary']
    p.write_text(json.dumps({'asof':'2026-11-19'}))
    data, issue = load_v2(tmp_path)
    assert data is None and 'dates differ' in issue

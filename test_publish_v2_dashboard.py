import csv
import json
from pathlib import Path
import pytest
from publish_v2_dashboard import FILES, COUNTRIES, validate, publish


def sample(tmp_path):
    d = tmp_path / 'data'; d.mkdir()
    summary = {'asof':'2026-11-20','mode':'SHADOW_ONLY_NO_ORDERS_NO_LINE',
               'country_universe':sorted(COUNTRIES),'bitcoin_proxy':'IBIT',
               'event_count':0,'qualified_countries':['INDA']}
    (d / FILES[2]).write_text(json.dumps(summary))
    (d / FILES[0]).write_text('Group,Ticker,AsOf,Signal\nCountry,INDA,2026-11-20,Confirmed Leader\n')
    (d / FILES[1]).write_text('Group,Ticker,Previous,Current,Event\n')
    (d / FILES[3]).write_text('Group,Ticker,AsOf,HybridScore,HybridStatus\nCountry,INDA,2026-11-20,100,Confirmed Leader\n')
    (d / FILES[4]).write_text('Ticker,HybridScore\nINDA,100\n')
    return d


def test_valid(tmp_path):
    assert validate(sample(tmp_path)) == '2026-11-20'


def test_missing_file(tmp_path):
    d=sample(tmp_path); (d / FILES[3]).unlink()
    with pytest.raises(ValueError, match='Missing'):
        validate(d)


def test_mismatched_dates(tmp_path):
    d=sample(tmp_path)
    p=d / FILES[3]; p.write_text(p.read_text().replace('2026-11-20','2026-11-19'))
    with pytest.raises(ValueError, match='AsOf'):
        validate(d)


def test_too_many_countries(tmp_path):
    d=sample(tmp_path)
    (d / FILES[4]).write_text('Ticker,HybridScore\nSPY,100\nEWJ,90\nINDA,80\nEWT,70\n')
    with pytest.raises(ValueError, match='shortlist'):
        validate(d)


def test_no_network_on_invalid_data(tmp_path):
    d=sample(tmp_path); (d / FILES[0]).unlink()
    def forbidden(*args, **kwargs):
        raise AssertionError('network should not be called')
    with pytest.raises(ValueError, match='Missing'):
        publish(d, 'token', opener=forbidden)


def test_no_token(tmp_path):
    with pytest.raises(ValueError, match='TOKEN'):
        publish(sample(tmp_path), '')

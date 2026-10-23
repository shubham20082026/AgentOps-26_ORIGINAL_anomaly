import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from reroute import config
from reroute.agent import investigate
from reroute.engine import Store
from reroute.fixtures import fixture


def test_database_relative_to_project(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ROOT', tmp_path)
    monkeypatch.setenv('REROUTE_DB', 'data/persistent.db')
    monkeypatch.chdir(tmp_path.parent)
    assert config.database_path() == tmp_path / 'data' / 'persistent.db'
    monkeypatch.setenv('REROUTE_DB', ':memory:')
    with pytest.raises(ValueError):
        config.database_path()


@pytest.mark.skipif(os.name != 'nt', reason='Windows DPAPI')
def test_key_encrypted_and_reloaded(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ROOT', tmp_path)
    for name in ('REROUTE_API_KEY', 'OPENAI_API_KEY', 'REROUTE_MODEL', 'REROUTE_API_URL'):
        monkeypatch.delenv(name, raising=False)
    config.save_api('test-only-secret', 'test-model', 'https://example.test/v1/chat/completions')
    raw = (tmp_path / '.private' / 'api.dpapi').read_bytes()
    assert b'test-only-secret' not in raw
    assert config.api_settings()['key'] == 'test-only-secret'
    assert config.api_settings()['model'] == 'test-model'
    monkeypatch.setenv('REROUTE_API_KEY', 'environment-secret')
    monkeypatch.setenv('REROUTE_MODEL', 'environment-model')
    assert config.api_settings()['key'] == 'environment-secret'
    (tmp_path / '.private' / 'api.dpapi').write_bytes(b'corrupted')
    assert config.api_settings()['key'] == 'environment-secret'
    monkeypatch.delenv('REROUTE_API_KEY')
    with pytest.raises(RuntimeError):
        config.api_settings()


@pytest.mark.parametrize('url', ['http://example.test', 'https://user:secret@example.test', 'https://', 'https://example.test/#secret'])
def test_bad_endpoint_rejected(url):
    with pytest.raises(ValueError):
        config.validate_endpoint(url)


def test_fresh_process_preserves_booking(tmp_path):
    db = tmp_path / 'restart.db'
    store = Store(db)
    cid = store.ingest(fixture('Happy path'))
    investigate(store, cid)
    c = store.get(cid)
    store.approve(cid, c['version'], c['plan']['fingerprint'], 'Test dispatcher')
    store.reserve(cid, c['version'], c['plan']['fingerprint'])
    store.reply(cid, c['version'], 'driver', 'accept')
    store.reply(cid, c['version'], 'recipient', 'accept')
    before = {'case': store.get(cid), 'holds': store.holds(cid), 'audit': store.audit(cid)}
    env = dict(os.environ, REROUTE_DB=str(db), PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    code = 'import json,sys; from reroute.engine import Store; s=Store(); c=sys.argv[1]; print(json.dumps(dict(case=s.get(c),holds=s.holds(c),audit=s.audit(c))))'
    result = subprocess.run([sys.executable, '-c', code, cid], cwd=tmp_path, env=env,
                            check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == before

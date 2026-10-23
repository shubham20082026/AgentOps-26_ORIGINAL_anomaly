import io
import json
from types import SimpleNamespace
import urllib.error
import pytest
from reroute.agent import completion, investigate, APIConnectionError
from reroute.engine import Store, WorkflowError
from reroute.fixtures import fixture


@pytest.mark.parametrize('status,expected', [(401,'key'), (404,'no longer available'), (429,'quota'), (503,'temporarily unavailable')])
def test_provider_error_is_actionable_and_redacted(monkeypatch, tmp_path, status, expected):
    monkeypatch.setenv('REROUTE_API_KEY', 'private-test-key')
    monkeypatch.setenv('REROUTE_MODEL', 'test-model')
    monkeypatch.setenv('REROUTE_API_URL', 'https://example.test/completions')
    def fail(*args, **kwargs):
        raise urllib.error.HTTPError('https://example.test',status,'private-test-key',{},io.BytesIO(b'private-test-key'))
    monkeypatch.setattr('urllib.request.build_opener',lambda *args: SimpleNamespace(open=fail))
    with pytest.raises(APIConnectionError, match=expected) as error:
        completion([], [])
    assert 'private-test-key' not in str(error.value)
    store=Store(tmp_path/'api-error.db')
    cid=store.ingest(fixture('Happy path'))
    with pytest.raises(WorkflowError, match=expected):
        investigate(store,cid,mode='llm')
    audit=json.dumps(store.audit(cid))
    assert 'private-test-key' not in audit
    assert expected in audit
    assert store.get(cid)['status']=='ESCALATED'

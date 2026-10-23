import pytest
from reroute import config
from reroute.evaluation import compare,stress_checks


def test_hosted_secrets_work_without_windows_credentials(monkeypatch,tmp_path):
    monkeypatch.setattr(config,'ROOT',tmp_path)
    for name in ('REROUTE_API_KEY','OPENAI_API_KEY','REROUTE_MODEL','REROUTE_API_URL','REROUTE_DB'):
        monkeypatch.delenv(name,raising=False)
    try:
        config.set_hosted_secrets(dict(REROUTE_API_KEY='hosted-test-key',REROUTE_MODEL='hosted-model',REROUTE_API_URL='https://example.test/completions'))
        assert config.api_settings()['key']=='hosted-test-key'
        assert config.api_settings()['model']=='hosted-model'
        monkeypatch.setenv('REROUTE_API_KEY','environment-key')
        assert config.api_settings()['key']=='environment-key'
    finally: config.set_hosted_secrets({})


def test_all_stress_checks():
    rows=stress_checks()
    assert len(rows)==5
    assert all(r['passed'] for r in rows),rows


def test_comparison_records_failures_instead_of_claiming_success():
    def broken(*args): raise TimeoutError('not a provider response')
    result=compare(1,True,transport=broken)
    assert result['summary'][0]['correct']==1
    assert result['summary'][1]['failures']==1
    assert result['summary'][1]['correct']==0
    assert result['summary'][1]['under_30_seconds']==0


@pytest.mark.parametrize('scenario',['Happy path','No capacity','Late arrival','Missing handling','Closed recipient','Driver unavailable'])
def test_baseline_comparison_correctness(scenario):
    result=compare(1,False,scenario)
    assert result['summary'][0]['correct']==1
    assert result['runs'][0]['trace']

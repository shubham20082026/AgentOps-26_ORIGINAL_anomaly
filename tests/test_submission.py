from types import SimpleNamespace
from evaluate import summarize
from reroute import config


def test_fast_failed_attempt_is_not_a_successful_latency_result():
    rows=[dict(scenario='Happy path',mode='llm',seconds=0.4,correct=False,failed=True),
          dict(scenario='Happy path',mode='llm',seconds=40.0,correct=True,failed=False)]
    report=summarize(rows)[0]
    assert report['median_seconds']==20.2
    assert report['min_seconds']==0.4 and report['max_seconds']==40.0
    assert report['successful_median_seconds']==40.0
    assert report['under_30_seconds']==0
    assert report['failures']==1


def test_build_revision_uses_checkout_and_handles_unavailable_git(monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='a'*40+'\n'))
    assert config.build_revision()=='a'*40
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='not-a-commit'))
    assert config.build_revision()=='unavailable'
    def missing(*a,**k):raise FileNotFoundError()
    monkeypatch.setattr(subprocess,'run',missing)
    assert config.build_revision()=='unavailable'

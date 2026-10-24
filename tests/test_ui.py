"""Headless browser-equivalent Streamlit widget workflow."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'

def click(at,label):
    next(b for b in at.button if b.label==label).click().run(timeout=60)
    assert not at.exception

def test_dispatcher_end_to_end(tmp_path,monkeypatch):
    monkeypatch.setenv('REROUTE_DB',str(tmp_path/'ui.db'))
    at=AppTest.from_file(str(APP)).run(timeout=60)
    assert not at.exception
    click(at,'Ingest cancellation')
    click(at,'Run recovery investigation')
    assert next(b for b in at.button if b.label=='Reserve approved capacity').disabled
    next(t for t in at.text_input if t.label=='Dispatcher approving this plan').input('Shubham').run()
    next(t for t in at.checkbox if t.label.startswith('I reviewed')).check().run()
    click(at,'Approve this version')
    click(at,'Reserve approved capacity')
    click(at,'Apply driver reply')
    assert any(m.value=='Awaiting Confirmations' for m in at.metric)
    click(at,'Apply recipient reply')
    assert any(m.value=='Confirmed' for m in at.metric)
    assert any(m.value=='24 boxes' and m.label=='Confirmed in sandbox' for m in at.metric)

def test_ui_stale_capacity(tmp_path,monkeypatch):
    monkeypatch.setenv('REROUTE_DB',str(tmp_path/'stale.db'))
    at=AppTest.from_file(str(APP)).run(timeout=60)
    click(at,'Ingest cancellation'); click(at,'Run recovery investigation')
    next(t for t in at.text_input if t.label=='Dispatcher approving this plan').input('Shubham').run()
    next(t for t in at.checkbox if t.label.startswith('I reviewed')).check().run()
    click(at,'Approve this version'); click(at,'Apply capacity change')
    assert any(m.value=='Open' for m in at.metric)
    click(at,'Run recovery investigation')
    assert any(m.value=='Escalated' for m in at.metric)


def test_fresh_demo_preserves_old_database(tmp_path,monkeypatch):
    from reroute.engine import Store
    monkeypatch.setenv('REROUTE_DB',str(tmp_path/'original.db'))
    at=AppTest.from_file(str(APP)).run(timeout=60)
    click(at,'Ingest cancellation')
    click(at,'Run recovery investigation')
    original=Store(tmp_path/'original.db').cases()
    click(at,'Start fresh demo')
    assert not at.exception
    assert Store(tmp_path/'original.db').cases()==original
    assert not at.selectbox(key='eval-scenario').value is None
    click(at,'Ingest cancellation')
    click(at,'Run recovery investigation')
    assert any(m.value=='Proposed' for m in at.metric)
    click(at,'Run comparison')
    assert at.session_state['evaluation']['summary'][0]['correct']==1
    click(at,'Run concurrency and recovery checks')
    assert all(r['passed'] for r in at.session_state['stress'])

def test_app_starts_with_cached_config_missing_optional_revision(tmp_path,monkeypatch):
    from reroute import config
    monkeypatch.setenv('REROUTE_DB',str(tmp_path/'cached-config.db'))
    monkeypatch.delattr(config,'build_revision',raising=False)
    at=AppTest.from_file(str(APP)).run(timeout=60)
    assert not at.exception
    assert any('reboot' in item.value.lower() for item in at.code)
    click(at,'Ingest cancellation')
    click(at,'Run recovery investigation')
    assert any(m.value=='Proposed' for m in at.metric)

def test_ui_retains_specific_quota_reason_after_rerun(tmp_path,monkeypatch):
    import reroute.agent as agent
    monkeypatch.setenv('REROUTE_DB',str(tmp_path/'quota-ui.db'))
    monkeypatch.setenv('REROUTE_API_KEY','test-key')
    monkeypatch.setenv('REROUTE_MODEL','test-model')
    def quota(*args):raise agent.APIConnectionError('API quota reached. Check provider usage.','quota','429')
    monkeypatch.setattr(agent,'completion',quota)
    at=AppTest.from_file(str(APP)).run(timeout=60)
    click(at,'Ingest cancellation')
    at.radio[0].set_value('LLM · configured API').run(timeout=60)
    click(at,'Run recovery investigation')
    click(at,'Refresh / check hold expiry')
    assert any('Quota:' in e.value for e in at.error)
    assert any(m.value=='Escalated' for m in at.metric)

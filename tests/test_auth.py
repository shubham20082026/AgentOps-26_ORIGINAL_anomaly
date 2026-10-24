import time
from pathlib import Path
from streamlit.testing.v1 import AppTest
from reroute import auth
APP=Path(__file__).resolve().parents[1]/'app.py'

def test_password_hash():
    encoded=auth.password_hash('sample-password-for-test')
    assert auth.verify('sample-password-for-test',encoded)
    assert not auth.verify('wrong',encoded)
    assert not auth.verify('wrong','malformed')

def test_login_logout_and_expiry(tmp_path,monkeypatch):
    auth._attempts.clear()
    db=tmp_path/'protected.db'
    monkeypatch.setenv('REROUTE_DB',str(db))
    monkeypatch.setenv('REROUTE_LOGIN_USER','dispatcher')
    monkeypatch.setenv('REROUTE_LOGIN_HASH',auth.password_hash('sample-password-for-test'))
    at=AppTest.from_file(str(APP)).run(timeout=60)
    assert not at.exception
    assert not db.exists()
    assert not any(b.label=='Ingest cancellation' for b in at.button)
    at.text_input[0].input('dispatcher'); at.text_input[1].input('wrong')
    at.button[0].click().run(timeout=60)
    assert any('incorrect' in e.value for e in at.error)
    assert not db.exists()
    at.text_input[0].input('dispatcher'); at.text_input[1].input('sample-password-for-test')
    at.button[0].click().run(timeout=60)
    assert not at.exception
    assert any(b.label=='Ingest cancellation' for b in at.button)
    at.session_state['_login_until']=time.time()-1
    at.run(timeout=60)
    assert not any(b.label=='Ingest cancellation' for b in at.button)
    at.text_input[0].input('dispatcher'); at.text_input[1].input('sample-password-for-test')
    at.button[0].click().run(timeout=60)
    next(b for b in at.button if b.label=='Sign out').click().run(timeout=60)
    assert not any(b.label=='Ingest cancellation' for b in at.button)
    assert not at.exception

def test_partial_settings_fail_closed(tmp_path,monkeypatch):
    db=tmp_path/'blocked.db'
    monkeypatch.setenv('REROUTE_DB',str(db))
    monkeypatch.setenv('REROUTE_LOGIN_USER','dispatcher')
    monkeypatch.setenv('REROUTE_LOGIN_HASH','malformed')
    at=AppTest.from_file(str(APP)).run(timeout=60)
    assert not at.exception
    assert not db.exists()
    assert not any(b.label=='Ingest cancellation' for b in at.button)

def test_throttle():
    auth._attempts.clear()
    assert all(auth.login_allowed() for _ in range(5))
    assert not auth.login_allowed()
    auth._attempts.clear()

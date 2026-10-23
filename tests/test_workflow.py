import concurrent.futures
import json
import threading
import pytest
from reroute.engine import Store, WorkflowError, check
from reroute.fixtures import fixture
from reroute.agent import investigate, Investigator

@pytest.fixture
def store(tmp_path): return Store(tmp_path/'test.db')

def proposed(store, scenario='Happy path'):
    cid=store.ingest(fixture(scenario))
    investigate(store,cid)
    return cid,store.get(cid)

def approved(store):
    cid,c=proposed(store)
    store.approve(cid,c['version'],c['plan']['fingerprint'],'Shubham')
    return cid,c

def test_happy_path_and_ten_replays(store):
    cid,c=approved(store)
    assert c['plan']['arrival']==862
    ids={store.reserve(cid,c['version'],c['plan']['fingerprint'])['id'] for _ in range(10)}
    assert len(ids)==1
    assert store.reply(cid,c['version'],'driver','accept')=='HELD'
    assert store.get(cid)['status']=='AWAITING_CONFIRMATIONS'
    assert store.reply(cid,c['version'],'recipient','accept')=='CONFIRMED'
    for _ in range(10): store.reply(cid,c['version'],'recipient','accept')
    assert store.get(cid)['status']=='CONFIRMED'
    assert len(store.holds(cid))==1
    assert len([a for a in store.audit(cid) if a['tool']=='verify_booking'])==1

@pytest.mark.parametrize('scenario',['No capacity','Late arrival','Missing handling','Closed recipient','Driver unavailable'])
def test_five_invalid_fixtures(store,scenario):
    cid,c=proposed(store,scenario)
    assert c['status']=='ESCALATED'
    assert not c['plan']
    assert not store.holds(cid)

def test_approval_required(store):
    cid,c=proposed(store)
    with pytest.raises(WorkflowError,match='approval'): store.reserve(cid,c['version'],c['plan']['fingerprint'])

def test_stale_version_cannot_approve_or_reserve(store):
    cid,c=approved(store)
    store.change_capacity(cid,'B',8)
    with pytest.raises(WorkflowError): store.approve(cid,c['version'],c['plan']['fingerprint'],'Shubham')
    with pytest.raises(WorkflowError): store.reserve(cid,c['version'],c['plan']['fingerprint'])
    investigate(store,cid)
    assert store.get(cid)['status']=='ESCALATED'
    assert store.get(cid)['approval'] is None

def test_tampered_fingerprint(store):
    cid,c=proposed(store)
    with pytest.raises(WorkflowError): store.approve(cid,c['version'],'tampered','Shubham')

@pytest.mark.parametrize('response',['decline','timeout'])
@pytest.mark.parametrize('party',['driver','recipient'])
def test_release_failure_and_reinvestigation(store,party,response):
    cid,c=approved(store)
    store.reserve(cid,c['version'],c['plan']['fingerprint'])
    assert store.reply(cid,c['version'],party,response)=='RELEASED'
    investigate(store,cid)
    assert store.get(cid)['status']=='ESCALATED'
    assert store.get(cid)['approval'] is None

def test_expiry_survives_restart(tmp_path):
    now=[1000.0]
    store=Store(tmp_path/'clock.db',clock=lambda:now[0])
    cid,c=approved(store)
    store.reserve(cid,c['version'],c['plan']['fingerprint'])
    now[0]+=121
    restarted=Store(store.path,clock=lambda:now[0])
    assert restarted.get(cid)['status']=='ESCALATED'
    assert restarted.holds(cid)[0]['status']=='EXPIRED'
    with pytest.raises(WorkflowError): restarted.reserve(cid,c['version'],c['plan']['fingerprint'])
    investigate(restarted,cid)
    fresh=restarted.get(cid)
    assert fresh['version']>c['version'] and fresh['approval'] is None

def test_concurrent_reservations_cannot_overbook(store):
    first,one=approved(store)
    second,two=approved(store)
    barrier=threading.Barrier(2)
    def book(pair):
        cid,c=pair
        barrier.wait()
        try: return store.reserve(cid,c['version'],c['plan']['fingerprint'])['id']
        except WorkflowError: return None
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results=list(pool.map(book,[(first,one),(second,two)]))
    assert sum(r is not None for r in results)==1

def test_concurrent_same_booking_is_idempotent(store):
    cid,c=approved(store)
    def book(_): return store.reserve(cid,c['version'],c['plan']['fingerprint'])['id']
    with concurrent.futures.ThreadPoolExecutor(5) as pool: ids=list(pool.map(book,range(10)))
    assert len(set(ids))==1

def test_capacity_change_releases_pending_hold(store):
    cid,c=approved(store)
    store.reserve(cid,c['version'],c['plan']['fingerprint'])
    store.change_capacity(cid,'B',8)
    assert store.holds(cid)[0]['status']=='RELEASED'
    with pytest.raises(WorkflowError): store.reply(cid,c['version'],'driver','accept')

def test_conflicting_reply_replay(store):
    cid,c=approved(store)
    store.reserve(cid,c['version'],c['plan']['fingerprint'])
    store.reply(cid,c['version'],'driver','accept')
    with pytest.raises(WorkflowError): store.reply(cid,c['version'],'driver','decline')

def test_agent_cannot_skip_evidence(store):
    cid=store.ingest(fixture())
    agent=Investigator(store,cid)
    with pytest.raises(WorkflowError): agent.call('propose',{'driver':'D2','recipient':'B'})
    agent.call('read_case',{})
    with pytest.raises(WorkflowError): agent.call('validate_pair',{'driver':'D2','recipient':'B'})
    with pytest.raises(WorkflowError): agent.call('approve',{})
    with pytest.raises(WorkflowError): agent.call('escalate',{'reason':'give up'})

def test_mock_llm_tool_protocol(store):
    cid=store.ingest(fixture())
    steps=[('read_case',{}),('inspect_driver',{'driver':'D2'}),('inspect_recipient',{'recipient':'A'}),
           ('validate_pair',{'driver':'D2','recipient':'A'}),('inspect_recipient',{'recipient':'B'}),
           ('validate_pair',{'driver':'D2','recipient':'B'}),('propose',{'driver':'D2','recipient':'B'})]
    def transport(messages,tools):
        if len(messages)>2: assert messages[-1]['role']=='tool'
        name,args=steps.pop(0)
        return {'content':None,'tool_calls':[{'id':str(len(steps)),'type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}
    investigate(store,cid,'llm',transport)
    assert store.get(cid)['status']=='PROPOSED'
    assert any(a['tool']=='tool_rejected' for a in store.audit(cid)) is False

def test_model_timeout_requires_explicit_retry(store):
    cid=store.ingest(fixture())
    def broken(*args): raise TimeoutError('mock')
    with pytest.raises(WorkflowError): investigate(store,cid,'llm',broken)
    assert store.get(cid)['status']=='ESCALATED'
    assert not store.holds(cid)
    investigate(store,cid)
    assert store.get(cid)['status']=='PROPOSED'

def test_bad_model_calls_are_bounded(store):
    cid=store.ingest(fixture())
    def bad(*args): return {'tool_calls':[{'id':'x','type':'function','function':{'name':'reserve','arguments':'{}'}}]}
    with pytest.raises(WorkflowError): investigate(store,cid,'llm',bad)
    assert store.get(cid)['status']=='ESCALATED'
    assert not store.holds(cid)

def test_boundary_arrival(store):
    data=fixture(); d=data['drivers'][1]; r=data['recipients'][1]
    d['travel']=30; r['closes']=870
    assert check(data,d,r)['valid']
    d['travel']=31
    assert not check(data,d,r)['valid']

def test_restart_persists_approval_and_audit(store):
    cid,c=approved(store)
    fresh=Store(store.path)
    assert fresh.get(cid)['approval']['actor']=='Shubham'
    assert fresh.audit(cid)==store.audit(cid)

def test_new_proposal_invalidates_old_fingerprint(store):
    cid,c=proposed(store)
    investigate(store,cid)
    with pytest.raises(WorkflowError): store.approve(cid,c['version'],c['plan']['fingerprint'],'Shubham')

def test_recovery_with_alternative(store):
    data=fixture(); data['drivers'][2]['capacity']=30
    cid=store.ingest(data); investigate(store,cid)
    c=store.get(cid)
    assert c['plan']['driver']=='D3'
    store.approve(cid,c['version'],c['plan']['fingerprint'],'Shubham')
    store.reserve(cid,c['version'],c['plan']['fingerprint'])
    store.reply(cid,c['version'],'driver','decline')
    investigate(store,cid)
    fresh=store.get(cid)
    assert fresh['plan']['driver']=='D2' and fresh['version']>c['version']
    assert fresh['approval'] is None

def test_http_adapter_payload(monkeypatch):
    from reroute.agent import completion
    monkeypatch.setenv('REROUTE_API_KEY','test-secret')
    monkeypatch.setenv('REROUTE_MODEL','configured-test-model')
    monkeypatch.setenv('REROUTE_API_URL','https://example.test/v1/chat/completions')
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,n): return b'{"choices":[{"message":{"content":null,"tool_calls":[]}}]}'
    def fake_urlopen(request,timeout):
        payload=json.loads(request.data)
        assert payload['model']=='configured-test-model'
        assert payload['tool_choice']=='required'
        assert request.get_header('Authorization')=='Bearer test-secret'
        assert timeout==30
        return Response()
    from types import SimpleNamespace
    monkeypatch.setattr('urllib.request.build_opener',lambda *args: SimpleNamespace(open=fake_urlopen))
    assert completion([],[])['tool_calls']==[]

def test_provider_error_does_not_log_secret(store):
    cid=store.ingest(fixture())
    def broken(*args): raise ValueError('sensitive-provider-secret')
    with pytest.raises(WorkflowError): investigate(store,cid,'llm',broken)
    assert 'sensitive-provider-secret' not in json.dumps(store.audit(cid))

def test_human_rejection_revokes_approval(store):
    cid,c=approved(store)
    store.reject(cid,c['version'],'Shubham','Need verified packaging evidence')
    assert store.get(cid)['approval'] is None
    assert store.get(cid)['status']=='ESCALATED'
    with pytest.raises(WorkflowError): store.reserve(cid,c['version'],c['plan']['fingerprint'])

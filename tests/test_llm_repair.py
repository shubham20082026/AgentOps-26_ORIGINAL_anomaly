import json
import pytest
from reroute.agent import Investigator, investigate
from reroute.engine import Store,WorkflowError
from reroute.fixtures import fixture


def call(name,args,identifier='call'):
    return {'id':identifier,'type':'function','function':{'name':name,'arguments':json.dumps(args)}}


def response(*calls):return {'role':'assistant','content':None,'tool_calls':list(calls)}


def names(agent):return {t['function']['name'] for t in agent.available_tools()}


def test_escalation_and_proposal_require_real_evidence(tmp_path):
    store=Store(tmp_path/'case.db');cid=store.ingest(fixture('No capacity'));a=Investigator(store,cid)
    assert names(a)=={'read_case'}
    a.call('read_case',{})
    assert names(a)=={'inspect_driver','inspect_recipient'}
    for d in ['D1','D2','D3']:a.call('inspect_driver',{'driver':d})
    for r in ['A','B']:a.call('inspect_recipient',{'recipient':r})
    assert names(a)=={'validate_pair'}
    for d in ['D1','D2','D3']:
        for r in ['A','B']:a.call('validate_pair',{'driver':d,'recipient':r})
    assert names(a)=={'escalate'}


def test_llm_can_choose_valid_pair_without_running_baseline(tmp_path,monkeypatch):
    store=Store(tmp_path/'case.db');cid=store.ingest(fixture('Recovery with alternate'))
    monkeypatch.setattr(Investigator,'deterministic',lambda self:pytest.fail('LLM silently fell back'))
    steps=[response(call('read_case',{})),response(call('inspect_driver',{'driver':'D2'},'d'),call('inspect_recipient',{'recipient':'B'},'r')),
        response(call('validate_pair',{'driver':'D2','recipient':'B'})),response(call('propose',{'driver':'D2','recipient':'B'}))]
    def transport(messages,tools):return steps.pop(0)
    investigate(store,cid,'llm',transport)
    c=store.get(cid)
    assert c['status']=='PROPOSED' and c['plan']['driver']=='D2'
    assert c['approval'] is None and not store.holds(cid)
    assert not steps


def test_model_can_batch_checks_and_escalate_in_four_rounds(tmp_path):
    store=Store(tmp_path/'case.db');cid=store.ingest(fixture('No capacity'))
    steps=[response(call('read_case',{})),
        response(*[call('inspect_driver',{'driver':d},d) for d in ['D1','D2','D3']],
                 *[call('inspect_recipient',{'recipient':r},r) for r in ['A','B']]),
        response(*[call('validate_pair',{'driver':d,'recipient':r},d+r) for d in ['D1','D2','D3'] for r in ['A','B']]),
        response(call('escalate',{'reason':'All six inspected pairs failed validation.'}))]
    def transport(messages,tools):return steps.pop(0)
    investigate(store,cid,'llm',transport)
    assert store.get(cid)['status']=='ESCALATED'
    assert any(e['tool']=='agent_completed' for e in store.audit(cid))
    assert not store.holds(cid) and not steps


def test_invalid_early_escalation_gets_progress_and_can_recover(tmp_path):
    store=Store(tmp_path/'case.db');cid=store.ingest(fixture())
    steps=[response(call('escalate',{'reason':'guess'})),response(call('read_case',{})),
        response(call('inspect_driver',{'driver':'D2'},'d'),call('inspect_recipient',{'recipient':'B'},'r')),
        response(call('validate_pair',{'driver':'D2','recipient':'B'})),response(call('propose',{'driver':'D2','recipient':'B'}))]
    attempts=[0]
    def transport(messages,tools):
        attempts[0]+=1
        if attempts[0]==2:
            feedback=json.loads(messages[-1]['content'])
            assert 'prerequisites' in feedback['error']
            assert feedback['progress']['case_read'] is False
        return steps.pop(0)
    investigate(store,cid,'llm',transport)
    assert store.get(cid)['status']=='PROPOSED'


def test_repeated_policy_errors_have_distinct_failure_category(tmp_path):
    store=Store(tmp_path/'case.db');cid=store.ingest(fixture())
    attempts=[0]
    def transport(*args):attempts[0]+=1;return response(call('reserve',{}))
    with pytest.raises(WorkflowError,match='three times'):investigate(store,cid,'llm',transport)
    details=json.loads(next(e['detail'] for e in store.audit(cid) if e['tool']=='agent_failed'))
    assert details['category']=='tool_policy' and details['code']=='repeated_rejections'
    assert attempts[0]==3 and not store.holds(cid)


def test_malformed_response_executes_no_partial_batch(tmp_path):
    store=Store(tmp_path/'case.db');cid=store.ingest(fixture())
    def transport(*args):return response(call('read_case',{}),{'function':{'name':'inspect_driver','arguments':'{}'}})
    with pytest.raises(WorkflowError,match='malformed'):investigate(store,cid,'llm',transport)
    assert not any(e['tool']=='read_case' for e in store.audit(cid))
    error=json.loads(next(e['detail'] for e in store.audit(cid) if e['tool']=='agent_failed'))
    assert error['category']=='protocol'


def test_changed_evidence_aborts_instead_of_reusing_old_approval(tmp_path):
    store=Store(tmp_path/'case.db');cid=store.ingest(fixture());attempts=[0]
    def transport(*args):
        attempts[0]+=1
        if attempts[0]==1:return response(call('read_case',{}))
        store.change_capacity(cid,'B',8)
        return response(call('inspect_driver',{'driver':'D2'}))
    with pytest.raises(WorkflowError,match='evidence changed'):investigate(store,cid,'llm',transport)
    error=json.loads(next(e['detail'] for e in store.audit(cid) if e['tool']=='agent_failed'))
    assert error['category']=='case_changed' and store.get(cid)['plan'] is None

def test_request_pacing_respects_configured_interval_without_exposing_key(monkeypatch):
    import reroute.agent as agent
    now=[100.0]; waits=[]
    monkeypatch.setattr(agent.time,'monotonic',lambda:now[0])
    def sleep(seconds):waits.append(seconds);now[0]+=seconds
    monkeypatch.setattr(agent.time,'sleep',sleep)
    monkeypatch.setattr(agent,'_last_request',{})
    settings=dict(url='https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',model='test',key='test-secret',min_interval='4.1')
    agent.pace_request(settings);agent.pace_request(settings)
    assert waits==pytest.approx([4.1])
    assert 'test-secret' not in repr(agent._last_request)


def test_invalid_pacing_configuration_is_classified(monkeypatch):
    from reroute.agent import pace_request,APIConnectionError
    with pytest.raises(APIConnectionError) as error:
        pace_request(dict(url='https://example.test',model='test',key='key',min_interval='nan'))
    assert error.value.category=='configuration'

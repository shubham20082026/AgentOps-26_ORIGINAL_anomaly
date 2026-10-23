"""Isolated, repeatable baseline/model comparisons and workflow stress checks."""
import concurrent.futures
import json
import statistics
import tempfile
import time
from pathlib import Path
from .agent import investigate
from .engine import Store, WorkflowError
from .fixtures import fixture

SCENARIOS = ['Happy path','No capacity','Late arrival','Missing handling','Closed recipient','Driver unavailable']
TOOL_NAMES = {'read_case','inspect_driver','inspect_recipient','validate_pair','propose','escalate'}


def compare(repeats=1, include_llm=False, scenario='Happy path', transport=None):
    if not 1 <= repeats <= 5 or scenario not in SCENARIOS:
        raise ValueError('Choose a known scenario and 1–5 repeats')
    rows=[]
    with tempfile.TemporaryDirectory(prefix='reroute-compare-') as folder:
        for mode in (['deterministic','llm'] if include_llm else ['deterministic']):
            for trial in range(repeats):
                store=Store(Path(folder)/f'{mode}-{trial}.db')
                cid=store.ingest(fixture(scenario))
                start=time.monotonic(); failure=False
                try: investigate(store,cid,mode,transport if mode=='llm' else None)
                except WorkflowError: failure=True
                elapsed=time.monotonic()-start
                case=store.get(cid); events=store.audit(cid)
                failures=[json.loads(e['detail']) for e in events if e['tool']=='agent_failed']
                expected='PROPOSED' if scenario=='Happy path' else 'ESCALATED'
                rows.append(dict(mode=mode,trial=trial+1,scenario=scenario,seconds=round(elapsed,4),
                    status=case['status'],correct=not failure and case['status']==expected,
                    failed=failure,failure_details=failures[-1] if failures else None,under_30_seconds=elapsed<30,
                    tool_calls=sum(e['tool'] in TOOL_NAMES and 'arguments' in json.loads(e['detail']) for e in events),
                    validations=sum(e['tool']=='validate_constraints' for e in events),
                    trace=[dict(tool=e['tool'],detail=json.loads(e['detail'])) for e in events if e['tool'] in TOOL_NAMES]))
    summary=[]
    for mode in dict.fromkeys(r['mode'] for r in rows):
        group=[r for r in rows if r['mode']==mode]
        summary.append(dict(mode=mode,runs=len(group),median_seconds=round(statistics.median(r['seconds'] for r in group),4),
            fastest_seconds=min(r['seconds'] for r in group),slowest_seconds=max(r['seconds'] for r in group),correct=sum(r['correct'] for r in group),
            failures=sum(r['failed'] for r in group),under_30_seconds=sum(r['under_30_seconds'] and not r['failed'] for r in group),
            mean_tool_calls=statistics.mean(r['tool_calls'] for r in group)))
    return dict(summary=summary,runs=rows,note='Synthetic inputs, isolated databases; proposal time excludes human approval. No LLM superiority is assumed.')


def approved(store, scenario='Happy path'):
    cid=store.ingest(fixture(scenario)); investigate(store,cid)
    c=store.get(cid); store.approve(cid,c['version'],c['plan']['fingerprint'],'Benchmark dispatcher')
    return cid,c


def stress_checks():
    results=[]
    with tempfile.TemporaryDirectory(prefix='reroute-stress-') as folder:
        store=Store(Path(folder)/'concurrent.db')
        cases=[approved(store) for _ in range(4)]
        def reserve(item):
            cid,c=item
            try: return store.reserve(cid,c['version'],c['plan']['fingerprint'])['id']
            except WorkflowError: return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            booked=list(pool.map(reserve,cases))
        results.append(dict(check='Simultaneous cancellations',passed=sum(bool(x) for x in booked)==1,
            evidence=f'{sum(bool(x) for x in booked)} of 4 competing cases reserved capacity (expected 1)'))
        winner=cases[next(i for i,x in enumerate(booked) if x)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            ids=list(pool.map(reserve,[winner]*10))
        results.append(dict(check='Duplicate reservation requests',passed=len(set(ids))==1 and None not in ids,
            evidence=f'{len(set(ids))} unique reservation across 10 repeated commands'))
        now=[1000.0]; store=Store(Path(folder)/'delay.db',clock=lambda:now[0])
        cid,c=approved(store); store.reserve(cid,c['version'],c['plan']['fingerprint'])
        store.reply(cid,c['version'],'driver','accept'); now[0]+=121
        expired=store.holds(cid)[0]['status']=='EXPIRED' and store.get(cid)['status']=='ESCALATED'
        another,plan=approved(store)
        released=store.reserve(another,plan['version'],plan['plan']['fingerprint'])['status']=='HELD'
        results.append(dict(check='Delayed confirmation',passed=expired and released,evidence='Clock advanced 121 seconds; hold expired and capacity was reusable'))
        store=Store(Path(folder)/'changed.db'); cid,c=approved(store)
        store.change_capacity(cid,'B',8)
        try: store.reserve(cid,c['version'],c['plan']['fingerprint']); blocked=False
        except WorkflowError: blocked=True
        investigate(store,cid)
        results.append(dict(check='Changing availability',passed=blocked and store.get(cid)['status']=='ESCALATED',evidence='Stale approval blocked; insufficient capacity escalated'))
        store=Store(Path(folder)/'replan.db'); cid,c=approved(store,'Recovery with alternate')
        first=c['plan']['driver']; store.reserve(cid,c['version'],c['plan']['fingerprint'])
        store.reply(cid,c['version'],'driver','decline'); investigate(store,cid)
        revised=store.get(cid)
        results.append(dict(check='Adaptive replanning',passed=revised['status']=='PROPOSED' and revised['plan']['driver']!=first and revised['approval'] is None,
            evidence=f"Declined {first}; proposed {revised['plan']['driver']} with fresh approval required"))
    return results

"""Offline, dependency-free rehearsal and measured evidence report."""
import json
import statistics
import tempfile
import time
from pathlib import Path
from reroute.engine import Store, WorkflowError
from reroute.agent import investigate
from reroute.fixtures import fixture

def run():
    report={'mode':'deterministic','synthetic':True,'live_provider_tested':False,'invalid_scenarios':{},'proposal_seconds':[]}
    with tempfile.TemporaryDirectory() as root:
        for n in range(10):
            store=Store(Path(root)/f'run{n}.db')
            cid=store.ingest(fixture())
            start=time.perf_counter(); investigate(store,cid)
            report['proposal_seconds'].append(round(time.perf_counter()-start,6))
            c=store.get(cid)
            assert c['plan']['arrival']==862
            store.approve(cid,c['version'],c['plan']['fingerprint'],'Rehearsal dispatcher')
            ids={store.reserve(cid,c['version'],c['plan']['fingerprint'])['id'] for _ in range(10)}
            assert len(ids)==1
            store.reply(cid,c['version'],'driver','accept')
            assert store.get(cid)['status']=='AWAITING_CONFIRMATIONS'
            store.reply(cid,c['version'],'recipient','accept')
            assert store.get(cid)['status']=='CONFIRMED'
            if n==0: report['sample_evidence']={'case':store.get(cid),'holds':store.holds(cid),'audit':store.audit(cid)}
        for n,name in enumerate(['No capacity','Late arrival','Missing handling','Closed recipient','Driver unavailable']):
            store=Store(Path(root)/f'invalid{n}.db'); cid=store.ingest(fixture(name)); investigate(store,cid)
            assert store.get(cid)['status']=='ESCALATED' and not store.holds(cid)
            report['invalid_scenarios'][name]='REJECTED / ESCALATED'
        store=Store(Path(root)/'recovery.db'); cid=store.ingest(fixture('Recovery with alternate')); investigate(store,cid)
        c=store.get(cid); assert c['plan']['driver']=='D3'
        store.approve(cid,c['version'],c['plan']['fingerprint'],'Rehearsal dispatcher')
        store.reserve(cid,c['version'],c['plan']['fingerprint']); store.reply(cid,c['version'],'driver','decline')
        investigate(store,cid); next_c=store.get(cid)
        assert next_c['plan']['driver']=='D2' and not next_c['approval'] and next_c['version']>c['version']
        report['failure_recovery']='D3 declined → released → D2 proposed; fresh approval required'
    report['proposal_median_seconds']=round(statistics.median(report['proposal_seconds']),6)
    report['proposal_max_seconds']=max(report['proposal_seconds'])
    report['repeated_reservations']=100
    report['unique_reservations']=10
    report['duplicate_reservations']=0
    return report

if __name__=='__main__':
    report=run()
    target=Path('rehearsal_report.json')
    target.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='sample_evidence'},indent=2))
    print(f'Full trace: {target.resolve()}')

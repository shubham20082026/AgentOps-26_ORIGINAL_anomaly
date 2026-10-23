"""Repeatable evaluation CLI. Uses local encrypted setup or environment credentials."""
import argparse
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from reroute.config import api_settings, build_revision
from reroute.evaluation import compare, stress_checks, SCENARIOS


def summarize(rows):
    result=[]
    for scenario in dict.fromkeys(r['scenario'] for r in rows):
        for mode in dict.fromkeys(r['mode'] for r in rows):
            group=[r for r in rows if r['scenario']==scenario and r['mode']==mode]
            if not group: continue
            times=[r['seconds'] for r in group]
            successful=[r['seconds'] for r in group if r['correct']]
            result.append(dict(scenario=scenario,mode=mode,runs=len(group),
                median_seconds=round(statistics.median(times),4),min_seconds=min(times),max_seconds=max(times),
                correct=sum(r['correct'] for r in group),failures=sum(r['failed'] for r in group),
                successful_median_seconds=round(statistics.median(successful),4) if successful else None,
                under_30_seconds=sum(r['correct'] and r['seconds']<30 for r in group)))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats',type=int,default=5,choices=range(1,6))
    parser.add_argument('--include-llm',action='store_true',help='Makes paid/quota-consuming provider requests; failures remain in the report')
    parser.add_argument('--output',default='evaluation_report.json')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    report=dict(schema_version=2,status='running',started_at=datetime.now(timezone.utc).isoformat(),
        source_commit=build_revision(),model=api_settings()['model'] if args.include_llm else None,
        trials_per_mode_per_scenario=args.repeats,scenario_count=len(SCENARIOS),runs=[],summary=[],
        code_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['reroute/agent.py','reroute/engine.py','reroute/evaluation.py','reroute/fixtures.py']},
        notes=['Identical synthetic inputs and isolated temporary databases. Approval time excluded.',
               'Serial trials without automatic retries or quota pacing. All attempts remain in the report.',
               'Fast failures are not successful recoveries. Repeat after provider quota resets when necessary.'])
    output=Path(args.output)
    def save():
        report['summary']=summarize(report['runs'])
        temporary=output.with_suffix('.tmp');temporary.write_text(json.dumps(report,indent=2),encoding='utf-8');temporary.replace(output)
    for trial in range(1,args.repeats+1):
        for scenario in SCENARIOS:
            result=compare(1,args.include_llm,scenario)
            for row in result['runs']:
                row['trial']=trial;report['runs'].append(row)
            save()
            print(f"Trial {trial}, {scenario}: checkpoint saved",flush=True)
    report['stress_checks']=stress_checks();report['status']='complete'
    report['completed_at']=datetime.now(timezone.utc).isoformat();save()


if __name__=='__main__': main()

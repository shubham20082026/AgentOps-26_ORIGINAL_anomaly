import json
import uuid
import os
from pathlib import Path
import streamlit as st
from reroute.agent import investigate, completion, tool_schema
from reroute.engine import Store, WorkflowError
from reroute.config import api_settings, database_path, set_hosted_secrets
from reroute import config as app_config
from reroute import agent as agent_module
from reroute.fixtures import SCENARIOS, fixture, hhmm

st.set_page_config(page_title='ReRoute | The rescue desk',page_icon='🌿',layout='wide')
st.markdown('''<style>
.stApp {background:#f7f3e9;color:#303c2d;background-image:radial-gradient(#8a75571a .55px,transparent .55px);background-size:7px 7px}
:root {--sand-muted:#63635e;--sand-border:#cfceca;--sand-ink:#21201c}
[data-testid="stSidebar"] {background:#ebe8d9;border-right:1px solid #d5d3be}
[data-testid="stHeader"] {background:#f7f3e9ed}
[data-testid="stMainBlockContainer"] {padding-top:2.7rem;max-width:1450px}
h1,h2,h3 {font-family:Georgia,'Times New Roman',serif!important;font-weight:400!important;letter-spacing:-.035em;color:#34452e}
h3 {font-size:1.55rem!important} p {line-height:1.65}
[data-testid="stCaptionContainer"] {color:var(--sand-muted)}
.eyebrow {color:#897057;font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.hero {display:flex;align-items:center;justify-content:space-between;gap:20px;padding:4px 0 26px;border-bottom:1px solid #c7cbb5;margin-bottom:22px}
.hero-copy {flex:1}.hero h1 {font-size:clamp(2.7rem,4.5vw,4.4rem);line-height:1.04;margin:16px 0 13px;padding:0}
.hero h1 em {color:#a65336;font-weight:400}.hero p {color:#6b705f;font-size:15px;max-width:440px;margin:0}
.hero-art {width:230px;flex-shrink:0;position:relative;text-align:center}
.hero-art svg {width:100%;height:auto}.art-note {font:italic 13px Georgia,serif;color:#87644a;transform:rotate(-4deg);margin-top:-12px}
.desk-brand {font:34px Georgia,serif;letter-spacing:-1.5px;color:#34452e;margin-bottom:5px}.desk-brand span {color:#a65336}
.desk-note {font:italic 14px Georgia,serif;color:#6f755f;margin:0 0 20px}
.desk-label {font-size:10px;letter-spacing:.17em;color:#81745d;margin-bottom:14px;font-weight:700}
[data-testid="stMetric"] {background:#fffdf5;border:1px solid #d6d7c3;border-top:3px solid #899770;border-radius:3px 12px 3px 12px;padding:17px 15px;box-shadow:0 3px 0 #e8e4d6}
[data-testid="stMetricLabel"] {color:#747762;font-size:12px}
[data-testid="stMetricValue"] {font-size:1.65rem;white-space:normal}
[data-testid="stMetricValue"] > div {font-family:Georgia,serif;color:#3f5035;white-space:normal;overflow-wrap:normal}
.stButton>button,.stDownloadButton>button {border-radius:5px 9px 5px 9px;border-color:#c5c9b4;box-shadow:0 2px 0 #d6d7c1;font-weight:500;transition:all .15s}
.stButton>button:hover,.stDownloadButton>button:hover {border-color:#a65336;color:#a65336;transform:translateY(-1px)}
.stButton>button[kind="primary"] {background:#a65336;border-color:#a65336;color:#fff9ed;box-shadow:0 3px 0 #86452e}
.stButton>button[kind="primary"]:hover {background:#91452d;color:#fff9ed}
.stButton>button:disabled {box-shadow:none;opacity:.5}
[data-baseweb="select"]>div,[data-baseweb="input"],[data-baseweb="base-input"] {background:#fffdf5!important;border-color:#c9ceb7!important;border-radius:6px!important;color:#303c2d!important}
[data-testid="stTextInput"] input {color:#303c2d!important}
[data-testid="stTabs"] [role="tablist"] {border-bottom:1px solid #d4d5be;gap:25px}
[data-testid="stTabs"] [role="tab"] {color:#777b64;padding-bottom:13px}
[data-testid="stTabs"] [aria-selected="true"] {color:#934b32;font-weight:600}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:#a65336}
[data-testid="stExpander"] {background:#efeddf;border-color:#d6d8c3;border-radius:7px}
[data-testid="stAlert"] {border-radius:5px 12px 5px 12px}
.journey {display:flex;align-items:center;justify-content:space-between;gap:10px;padding:14px 0 20px;margin-bottom:15px;border-bottom:1px solid #d6d8c3;color:#7c806a;font-size:12px}
.journey span {display:flex;align-items:center;gap:8px}.journey b {display:inline-grid;place-items:center;width:25px;height:25px;border:1px solid #b9c0a2;border-radius:50%;font-weight:400;font-family:Georgia,serif}
.journey .done {color:#4e6540}.journey .done b {background:#e2e8d6;border-color:#a0b18b}
.journey .current {color:#934b32;font-weight:600}.journey .current b {background:#a65336;border-color:#a65336;color:#fff9ed}
hr {border-color:#d3d4bd!important}
@media(max-width:900px) {.hero-art {width:150px}.hero h1 {font-size:2.8rem}.hero p {font-size:14px}}
@media(max-width:600px) {.hero-art {display:none}.hero h1 {font-size:2.8rem}[data-testid="stMainBlockContainer"] {padding:2rem 1rem}}

/* Dark forest accents keep the warm workspace readable. */
[data-testid="stSidebar"] button p {color:inherit!important}
[data-testid="stSidebar"] {background:#202c29;border-right:1px solid #36453e;color:#f2ecdf}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] .desk-note {color:#c6cebd!important}
[data-testid="stSidebar"] .desk-brand {color:#fff5df}
[data-testid="stSidebar"] .desk-brand span {color:#e4a878}
[data-testid="stSidebar"] .desk-label {color:#aab99b}
[data-testid="stSidebar"] hr {border-color:#46544a!important}
[data-testid="stSidebar"] [data-testid="stExpander"] {background:#2d3b34;border-color:#4c5b4e;color:#f6efdf}
[data-testid="stSidebar"] .stButton>button {background:#34463b!important;color:#f5efdf!important;border-color:#5a6b56;box-shadow:none}
[data-testid="stSidebar"] .stButton>button:hover {background:#455e48;border-color:#c29b72;color:white}
[data-testid="stSidebar"] [data-baseweb="select"]>div {background:#f6f0e4!important;color:#24372b!important}
.hero {background:#27382e;border:1px solid #354a3a;border-radius:16px;padding:30px 34px;margin-bottom:26px}
.hero h1 {color:#fff5df}.hero h1 em {color:#dfa47c}.hero p {color:#d2d8c7}.hero .eyebrow {color:#becaab}.hero .art-note {color:#dac4a3}
[data-testid="stMetric"] {border-top:4px solid #293e30;box-shadow:0 3px 0 #dfdfd0}
.stButton>button[kind="primary"] {background:#304a36;border-color:#304a36;box-shadow:0 3px 0 #1c3021}
.stButton>button[kind="primary"]:hover {background:#425f3d;color:#fff9ed}
[data-testid="stTabs"] [aria-selected="true"] {color:#294a32}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:#294a32}
.login-banner {background:#23372b;color:#eee9d9;padding:44px;border-radius:18px;margin:15px 0 36px}
.login-banner > span {font-size:11px;letter-spacing:.18em;color:#b8c4a4}
.login-banner h1 {color:#fff2d8;font-size:3.6rem;margin:16px 0 8px}
.login-banner p {color:#cfdbc4;margin:0}
@media(max-width:600px){.hero {padding:24px 20px}.login-banner {padding:28px}}

</style>''',unsafe_allow_html=True)
try:
    hosted_secrets=dict(st.secrets)
except FileNotFoundError:
    hosted_secrets={}
set_hosted_secrets(hosted_secrets)
from reroute.auth import gate
signed_in_user=gate(st, hosted_secrets)
store=Store(st.session_state.get('demo_db', database_path()))

def action(fn):
    try:
        fn()
        st.rerun()
    except WorkflowError as exc: st.error(str(exc))

with st.sidebar:
    st.markdown('<div class="desk-label">THE FOOD RESCUE DESK</div><div class="desk-brand">ReRoute<span>↗</span></div><div class="desk-note">Good food deserves a second chance.</div>',unsafe_allow_html=True)
    st.caption('ORIGINAL_anomaly · Shubham Parmar')
    st.divider()
    if st.button('Start fresh demo', help='Create an isolated demo database. Previous records are preserved.'):
        st.session_state.demo_db=str(database_path().parent/('demo-'+uuid.uuid4().hex+'.db'))
        st.session_state.pop('cid',None)
        st.rerun()
    st.caption('Fresh demos preserve previous records and start with unused capacity.')
    scenario=st.selectbox('Synthetic scenario',list(SCENARIOS))
    st.caption(SCENARIOS[scenario])
    if st.button('Ingest cancellation',type='primary',width='stretch'):
        st.session_state.cid=store.ingest(fixture(scenario)); st.rerun()
    rows=store.cases()
    if rows:
        ids=[r['id'] for r in rows]
        selected=st.selectbox('Persistent case inbox',ids,index=ids.index(st.session_state.get('cid',ids[0])) if st.session_state.get('cid') in ids else 0)
        st.session_state.cid=selected
    mode=st.radio('Investigation mode',['Deterministic · offline','LLM · configured API'])
    try:
        settings=api_settings()
        api_ready=bool(settings['key'] and settings['model'])
        st.caption('API configured' if api_ready else 'API setup needed. Offline mode works immediately.')
        del settings
    except Exception:
        api_ready=False
        st.warning('API settings could not be loaded. Check hosted Secrets or local API setup.')
    with st.expander('Hosted API setup'):
        st.write('In Streamlit: Manage app → Settings → Secrets. Add REROUTE_API_KEY, REROUTE_MODEL and REROUTE_API_URL. See CLOUD_SETUP.md for the template. Local Windows credentials are not transferred to the hosted app.')
    st.caption('SQLite saves this demo on the current server. Cloud rebuilds can replace local files; use durable storage for production.')
    if st.button('Test API connection',disabled=not api_ready):
        try:
            with st.spinner('Checking provider tool calling…'):
                result=completion([{'role':'user','content':'Call connection_check.'}],[tool_schema('connection_check','Verify tool calling.',[])])
            if any(call.get('function',{}).get('name')=='connection_check' for call in result.get('tool_calls',[])):
                st.success('API connected; tool calling works.')
            else:
                st.warning('Provider responded without the required tool call. Check model support.')
        except WorkflowError as exc:
            st.error(str(exc))
        except Exception:
            st.error('Provider response could not be read. Check the endpoint and model.')
    st.caption('Offline mode is a rule-based tool loop. LLM mode chooses tools; Python enforces every safety check.')
    with st.expander('Build and deployment'):
        revision=getattr(app_config,'build_revision',lambda:'unavailable — reboot the app to load the updated module')()
        st.code(revision,language=None)
        st.caption('LLM controller: state-aware tools' if hasattr(agent_module.Investigator,'available_tools') else 'Legacy LLM controller loaded — reboot after updating.')
        st.caption('Compare this checkout revision with the GitHub commit before the submission freeze.')
    st.divider()
    st.markdown('**AgentOps 2026 · 24 October**')
    st.caption('Transport / Retail and Supply\n\nSandbox only. No live maps, messaging, food-safety certification or delivery integration.')

st.markdown('''<div class="hero"><div class="hero-copy"><span class="eyebrow">A SMALL DETOUR. A LITTLE MORE POSSIBILITY.</span><h1>Good food.<br><em>Another way home.</em></h1><p>A pickup fell through. Let’s find a thoughtful, checked replacement — and make sure everyone is on board.</p></div><div class="hero-art">
<svg viewBox="0 0 250 210" xmlns="http://www.w3.org/2000/svg" fill="none" aria-label="Line drawing of a food crate with vegetables and a winding route" role="img">
<ellipse cx="128" cy="181" rx="90" ry="8" fill="#dedcc5"/>
<path d="M14 143C-3 102 38 89 60 102S72 153 111 140 141 80 195 72" stroke="#acb08a" stroke-width="2" stroke-dasharray="4 6" stroke-linecap="round"/>
<circle cx="16" cy="143" r="5" fill="#a65336"/><path d="m185 66 14 5-8 12" stroke="#a65336" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M80 116C67 93 65 65 81 52c17 7 19 30 12 48" fill="#a5b18a" stroke="#5e704b" stroke-width="2"/>
<path d="m82 67 7 49M82 83l-8-8m12 20 8-11" stroke="#5e704b" stroke-width="1.7" stroke-linecap="round"/>
<path d="M105 112c-9-16-2-32 12-34 3-21 24-24 34-11 20-1 26 21 15 33l-5 15" fill="#c1c8a2" stroke="#5e704b" stroke-width="2"/>
<path d="m135 86-1 33m0-18-13-10m13 16 16-17" stroke="#72845b" stroke-width="2" stroke-linecap="round"/>
<path d="M163 112c-3-14 4-24 16-23s20 14 12 27" fill="#bd7253" stroke="#965339" stroke-width="2"/>
<path d="m176 92 4-8m-7 4 7 3 7-3" stroke="#5e704b" stroke-width="2" stroke-linecap="round"/>
<path d="m61 113 139-2-12 64-115 2Z" fill="#e9d4ac" stroke="#8b7854" stroke-width="2.4" stroke-linejoin="round"/>
<path d="m64 126 133-2m-130 18 126-2m-123 18 119-2M86 114l7 62m79-64-9 63" stroke="#aa9165" stroke-width="2"/>
<rect x="111" y="131" width="39" height="29" rx="2" fill="#f7f3e9" stroke="#a6a17a" transform="rotate(-5 111 131)"/>
<path d="m122 147 15-1m-5-5 6 5-5 6" stroke="#a65336" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="m211 126 3-8 3 8 8 3-8 3-3 8-3-8-8-3Z" fill="#b4ba95"/>
</svg><div class="art-note">a second chance, carefully carried</div></div></div>''',unsafe_allow_html=True)
from reroute.evaluation_ui import render_evaluation
render_evaluation(api_ready)
if not rows:
    st.info('Start in the sidebar: ingest the Happy path cancellation. The complete demo needs no API key.')
    st.stop()
cid=st.session_state.cid
c=store.get(cid); data=c['data']; plan=c['plan']; holds=store.holds(cid)
st.caption(f"{cid} · Case version {c['version']} · {data['scenario']} · All travel times and replies are synthetic")
cols=st.columns(4)
cols[0].metric('Donation at risk',f"{data['boxes']} boxes")
cols[1].metric('Food deadline',hhmm(data['deadline']))
cols[2].metric('Recovery status',c['status'].replace('_',' ').title())
cols[3].metric('Confirmed in sandbox',f"{data['boxes'] if c['status']=='CONFIRMED' else 0} boxes")
st.write('')
stages=['Cancellation','Investigation','Your approval','Reservation','Both replies']
position={'OPEN':1,'PROPOSED':2,'APPROVED':3,'AWAITING_CONFIRMATIONS':4,'CONFIRMED':5,'ESCALATED':1}[c['status']]
st.markdown('<div class="journey">'+''.join(f'<span class="{"done" if i<position else "current" if i==position else ""}"><b>{"✓" if i<position else i+1}</b>{name}</span>' for i,name in enumerate(stages))+'</div>',unsafe_allow_html=True)
ops,evidence,audit,about=st.tabs(['Recovery workspace','Evidence & constraints','Audit & export','How it works'])
with ops:
    left,right=st.columns([1.35,1])
    with left:
        st.subheader('01 / Find another way')
        st.write(data['cancellation'])
        st.caption(f"{data['donor']} · {data['handling']} · Fixed pickup {hhmm(data['pickup'])}")
        if st.button('Run recovery investigation',type='primary',disabled=c['status'] not in ('OPEN','PROPOSED','ESCALATED') or (mode.startswith('LLM') and not api_ready)):
            with st.spinner('Inspecting resources and checking replacement pairs…'):
                action(lambda: investigate(store,cid,'llm' if mode.startswith('LLM') else 'deterministic'))
        case_events=store.audit(cid)
        starts=[i for i,e in enumerate(case_events) if e['tool']=='agent_started']
        latest=case_events[starts[-1]:] if starts else []
        finished=[json.loads(e['detail']) for e in latest if e['tool']=='agent_completed']
        if finished:
            st.caption(f"Last investigation: {finished[-1]['mode']} · {finished[-1]['elapsed_seconds']:.2f} seconds · approval excluded")
        if c['status']=='ESCALATED':
            failed=[json.loads(e['detail']) for e in latest if e['tool']=='agent_failed']
            if failed:
                failure=failed[-1]
                category=failure.get('category','investigation').replace('_',' ').title()
                st.error(category+': '+failure.get('reason','Review the recorded error and retry.'))
            else:
                reasons=[json.loads(e['detail']).get('reason') for e in reversed(case_events) if e['tool'] in ('escalate','release_and_escalate')]
                st.warning(next((r for r in reasons if r), 'Investigation stopped. Review evidence and retry.'))
            st.info('If this is a repeated demo, earlier bookings may consume capacity. Choose Start fresh demo for an isolated run.')
        with st.expander('Investigation decisions and evidence'):
            for e in latest:
                if e['tool'] in ('read_case','inspect_driver','inspect_recipient','validate_pair','propose','escalate','tool_rejected'):
                    st.write(e['tool'].replace('_',' ').title())
                    st.json(json.loads(e['detail']))
        st.subheader('02 / Give the plan a human check')
        if plan:
            st.markdown(f"### {plan['driver']} → Campus pickup → {plan['recipient']}")
            st.write(f"Carry **{plan['boxes']} boxes** · Fixture arrival **{hhmm(plan['arrival'])}** · Deadline slack **{data['deadline']-plan['arrival']} minutes**")
            st.caption(f"Approval binds version {c['version']} and plan fingerprint {plan['fingerprint'][:16]}…")
            actor=signed_in_user or st.text_input('Dispatcher approving this plan',placeholder='Enter your name',key=f'actor-{cid}')
            if signed_in_user: st.caption('Approval identity: '+signed_in_user)
            reviewed=st.checkbox('I reviewed capacity, handling evidence, arrival and receiving window.',key=f'review-{cid}-{c["version"]}')
            if st.button('Approve this version',disabled=c['status']!='PROPOSED' or not reviewed or not actor.strip()):
                action(lambda:store.approve(cid,c['version'],plan['fingerprint'],actor))
            if c['approval']: st.success(f"Approved by {c['approval']['actor']} for version {c['approval']['version']}")
            with st.expander('Reject this proposal / request manual review'):
                reason=st.text_input('Reason for rejection',key=f'reject-{cid}-{c["version"]}')
                if st.button('Reject and escalate',disabled=c['status'] not in ('PROPOSED','APPROVED') or not actor.strip() or not reason.strip()):
                    action(lambda:store.reject(cid,c['version'],actor,reason))
        else: st.info('Investigation will produce a checked proposal or explicit escalation.')
    with right:
        st.subheader('03 / Reserve & verify')
        st.write('A reservation consumes shared sandbox capacity for 120 seconds. A booking is confirmed only after both simulated replies accept.')
        if st.button('Reserve approved capacity',disabled=c['status'] not in ('APPROVED','AWAITING_CONFIRMATIONS','CONFIRMED')):
            action(lambda:store.reserve(cid,c['version'],plan['fingerprint']))
        if holds:
            h=holds[-1]
            st.write(f"**Reservation:** {h['status']} · v{h['version']}")
            for party in ('driver','recipient'):
                st.caption(f"{party.title()} reply: {h[party+'_reply'] or 'pending'}")
            if h['status']=='HELD':
                st.warning('Simulation controls — these do not send real messages.')
                for party in ('driver','recipient'):
                    response=st.selectbox(f'Simulated {party} response',['accept','decline','timeout'],index=['accept','decline','timeout'].index(data['replies'][party]),key=f'{party}-{h["id"]}')
                    if st.button(f'Apply {party} reply',disabled=bool(h[party+'_reply'])):
                        action(lambda party=party,response=response:store.reply(cid,c['version'],party,response))
        if c['status']=='CONFIRMED':
            st.success('Both parties accepted. Sandbox booking verified and persisted.')
            st.caption('This proves workflow completion, not a real delivery or food saved.')
        with st.expander('Failure lab · change recipient B capacity'):
            st.caption('Invalidates approval, releases any pending hold and increments the case version. Use 8 to reproduce stale capacity.')
            cap=st.number_input('New capacity',min_value=0,max_value=100,value=8,step=1)
            if st.button('Apply capacity change',disabled=c['status']=='CONFIRMED'):
                action(lambda:store.change_capacity(cid,'B',int(cap)))
        if st.button('Refresh / check hold expiry'): st.rerun()
with evidence:
    st.subheader('Evidence comes from synthetic tools')
    st.caption('Capacities share resource IDs across cases. Active holds and confirmed bookings consume capacity. ETA = fixed pickup + fixture travel; no map service.')
    st.dataframe(data['recipients'],width='stretch',hide_index=True)
    st.dataframe(data['drivers'],width='stretch',hide_index=True)
    validations=[json.loads(a['detail']) for a in store.audit(cid) if a['tool']=='validate_constraints']
    if validations:
        st.subheader('Deterministic validation results')
        st.dataframe([dict(driver=v['driver'],recipient=v['recipient'],arrival=hhmm(v['arrival']),valid=v['valid'],reason='; '.join(v['reasons']) or 'All checks passed') for v in validations],hide_index=True,width='stretch')
with audit:
    events=store.audit(cid)
    st.subheader(f'{len(events)} persisted events')
    st.download_button('Download case evidence JSON',json.dumps({'case':c,'holds':holds,'audit':events},indent=2),file_name=f'{cid}-evidence.json',mime='application/json')
    for event in reversed(events):
        with st.expander(f"#{event['seq']} · v{event['version']} · {event['tool']}"):
            st.json(json.loads(event['detail']))
with about:
    st.markdown('''### A bounded agent, checked by code
The investigator reads the cancellation, inspects driver and recipient evidence, validates alternatives, and proposes a feasible plan. Rejection changes the next investigation: the failed party is excluded. If all options fail, the case escalates.

**LLM mode:** a configured tool-capable model selects the investigation tools. It has no approval, reservation or confirmation tool. Timeouts, malformed calls and budgets stop the run for manual review.

**Deterministic mode:** a functional rule-based controller calls the same tools and selects the earliest feasible pair. It is not an LLM and does not claim generative reasoning.

**Actually working:** SQLite transactions, shared capacity accounting, exact-version approvals, unique reservation keys, repeat-safe replies, expiry, release, persistent audit, evidence export and failure recovery.

**Simulated:** cancellations, resource availability, handling evidence, fixed travel times, driver replies and recipient replies. No real food rescue, GPS, SMS, NGO or vehicle booking integration is claimed.

**Hackathon scope:** one whole donation, one driver, one recipient. Food safety is represented by synthetic handling flags; no production certification. Local dispatcher name is attribution, not authentication. Confirmed allocations remain consumed until an operational completion workflow is built.
''')


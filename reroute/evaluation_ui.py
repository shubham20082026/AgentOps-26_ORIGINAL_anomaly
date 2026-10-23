"""Evaluation controls use isolated temporary databases, never dispatcher bookings."""
import json
import streamlit as st
from .evaluation import compare, stress_checks, SCENARIOS


def render_evaluation(api_ready):
    with st.expander('Evaluation lab · baseline comparison and failure recovery'):
        st.write('Measure the rule-based baseline and optional LLM on identical synthetic inputs. Compare correctness, proposal latency and investigation effort. These experiments do not prove the LLM is better.')
        scenario=st.selectbox('Comparison scenario',SCENARIOS,key='eval-scenario')
        repeats=st.number_input('Trials per mode',min_value=1,max_value=5,value=1,key='eval-trials')
        include=st.checkbox('Include live LLM comparison (uses provider quota)',disabled=not api_ready,key='eval-live')
        if st.button('Run comparison'):
            with st.spinner('Running isolated comparison trials…'):
                st.session_state.evaluation=compare(int(repeats),bool(include),scenario)
        if 'evaluation' in st.session_state:
            report=st.session_state.evaluation
            st.dataframe(report['summary'],hide_index=True,width='stretch')
            st.caption(report['note'])
            st.download_button('Download comparison JSON',json.dumps(report,indent=2),file_name='reroute-comparison.json',mime='application/json')
            st.json(report['runs'],expanded=False)
        if st.button('Run concurrency and recovery checks'):
            st.session_state.stress=stress_checks()
        if 'stress' in st.session_state:
            st.dataframe(st.session_state.stress,hide_index=True,width='stretch')
            st.caption('Delayed confirmation uses an injected clock; no actual two-minute wait. Concurrency uses four cases competing for the same resources. These checks exercise deterministic transaction safeguards.')

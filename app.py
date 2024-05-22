import streamlit as st
from multiapp import MultiApp
from apps import home, data_checking, clinical_qc, uploadSystem, data_visualization, hy_qc
# https://gp2qc-uploadvis-wskofeynza-uc.a.run.app/

st.set_page_config(layout="wide")

if 'smqc' not in st.session_state:
    st.session_state['smqc'] = None
if 'clinqc' not in st.session_state:
    st.session_state['clinqc'] = None
if 'hyqc' not in st.session_state:
    st.session_state['hyqc'] = None
if 'master_get' not in st.session_state:
    st.session_state['master_get'] = None
if 'all_ids' not in st.session_state:
    st.session_state['all_ids'] = None

app = MultiApp()
st.markdown(""" 
# GP2 clinical cohort self checking and upload system
"""
)

app.add_app("Home", home.app)
app.add_app("sample manifest", data_checking.app)
app.add_app("clinical data", clinical_qc.app)
app.add_app("clinical data (hoehn and yahr)", hy_qc.app)
app.add_app("Upload", uploadSystem.app)
app.add_app("Visualization", data_visualization.app)
# Run the main app
app.run()

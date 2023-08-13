import streamlit as st
from multiapp import MultiApp
from apps import home, data_checking, uploadSystem, data_visualization

st.set_page_config(layout="wide")

# Initialise dfqc in session state to move across tabs
if 'allqc' not in st.session_state:
    st.session_state['allqc'] = None
if 'smqc' not in st.session_state:
    st.session_state['smqc'] = None
if 'clinqc' not in st.session_state:
    st.session_state['clinqc'] = None
if 'dct_tmplt' not in st.session_state:
    st.session_state['dct_tmplt'] = None

app = MultiApp()
st.markdown(""" 
# GP2 clinical cohort self checking and upload system
"""
)

app.add_app("Home", home.app)
app.add_app("QC", data_checking.app)
app.add_app("Upload", uploadSystem.app)
app.add_app("Visualization", data_visualization.app)
# Run the main app
app.run()

import streamlit as st
from multiapp import MultiApp
from apps import home, data_checking, uploadSystem

st.set_page_config(layout="wide")

# Initialise dfqc in session state to move across tabs
if 'dfqc' not in st.session_state:
    st.session_state['dfqc'] = 'NULL'

app = MultiApp()
st.markdown(""" 
# GP2 clinical cohort self checking and upload system
"""
)

app.add_app("Home", home.app)
app.add_app("QC", data_checking.app)
app.add_app("Upload", uploadSystem.app)
# Run the main app
app.run()

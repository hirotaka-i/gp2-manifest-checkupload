import streamlit as st
import streamlit.components.v1 as stc

# File Processing Pkgs
import pandas as pd
import numpy as np
import base64
import datetime as dt
from multiapp import MultiApp
from apps import home, data_checking, uploadSystem

st.set_page_config(layout="wide")

today = dt.datetime.today()
version = f'{today.year}{today.month}{today.day}'
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


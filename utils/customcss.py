import streamlit as st
def load_css(file_name = "/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/apps/css/css.css"):
   with open(file_name) as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
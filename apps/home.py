try:
    import streamlit as st
    from PIL import Image
    import sys
    sys.path.append('utils')
    from customcss import load_css
except Exception as e:
    print("Some modules are not installed {}".format(e))

def app():
    #load_css("/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/apps/css/css.css")
    load_css("/app/apps/css/css.css")
    st.markdown('<p class="big-font">Welcome to the GP2 Complex Hub QC and Upload system</p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font">At the top, you can find navigation bar</p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Please, move to the QC bar to do the guided data QC. </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Once the QC is completed, download the file and move to the Upload bar to store your manifest on a \
        GP2 managed storage system</p>', unsafe_allow_html=True)
    
    st.write("##")
    st.write("##")

    image = Image.open('apps/img/GP2_logo_color.png')
    head_1, gp2_logo, head_3 = st.columns([0.6, 1, 0.6])
    gp2_logo.image(image, width=600)
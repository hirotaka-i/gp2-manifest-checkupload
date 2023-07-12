try:
    import streamlit as st
    from PIL import Image
except Exception as e:
    print("Some modules are not installed {}".format(e))

def app():
    st.markdown("""
    <style>
    .big-font {
        font-family:Helvetica; color:#0f557a; font-size:48px !important;
    }
    .medium-font {
        font-family:Arial; color:000000; font-size:18px;
    }
    div.stButton > button:first-child {
        background-color: #D3D3D3;
        height: auto;
        color: black;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        font-size: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

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

    st.write("##")
    
    if st.button('Show me the video demo'):
        side = max((100 - 80) / 2, 0.01)
        _, container, _ = st.columns([side, 80, side])
        container.video(data='apps/vid/demo.webm')
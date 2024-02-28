try:
    import os
    import streamlit as st
    import sys
    import re
    sys.path.append('utils')
    from customcss import load_css
    from writeread import upload_data, read_file, get_studycode, email_ellie
    from plotting import aggridPlotter
except Exception as e:
    print("Some modules are not installed {}".format(e))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "secrets/secrets.json"

def app():
    load_css("apps/css/css.css")
    st.markdown('<p class="big-font"> GP2 Sample Uploader System</p>', unsafe_allow_html=True)

    source_file = st.sidebar.file_uploader("Upload the QC Sample Manifest",
                                            type=['xlsx'])

    study_name = get_studycode() # This will set study_name to None when initialised
    if 'keepcode' in st.session_state:
        if len(re.findall(r'-', st.session_state['keepcode']))>0:
            study_name = st.session_state['keepcode'].split('-')[0]

    # Add preview util
    if source_file is not None:
        file_details = {"FileName":source_file.name,
                        "FileType":source_file.type,"FileSize":source_file.size}
        file_name, file_extension = os.path.splitext(file_details["FileName"])

        # Get whether clinical or sm file
        if re.match('.*clinial_data.*', file_name):
            whatfile = 'clinical'
            n_cols = 7
        elif re.match('.*sample_manifest.*', file_name):
            whatfile = 'sampleManifest'
            n_cols = 35
        else:
            st.error('This file does not seem to be QCed')
            st.error('Please go back to the sample manifest and/or clinical tab and QC your file')
            st.error('Ciao')
            st.stop()

        df = read_file(source_file)
        
        aggridPlotter(df)
        
        manifest_check = st.selectbox(
            "Does the format look correct",
            options = ["Yes", "No"],
            index = None,
            key = 1
        )

        # Add uploader button
        if st.button("Upload to GP2 Google Cloud Bucket"):
            if whatfile == 'sampleManifest':
                df[['sample_id', 'clinical_id', 'SampleRepNo']] = df[['sample_id','clinical_id', 'SampleRepNo']].astype(str)
                if st.session_state['smqc'] is not None:
                    checkdf = True if df.shape == st.session_state['smqc'].shape else False     
                else:
                    checkdf = True if df.shape[1] == n_cols else False
            elif whatfile == 'clinical':
                try:
                    df[['sample_id']] = df[['sample_id']].astype(str)
                    comp = df.compare(st.session_state['clinqc'])
                    checkdf = True if comp.shape == (0, 0) else False 
                except:
                    checkdf = True if df.shape[1] == n_cols else False

            if checkdf:
                if study_name:
                    if manifest_check == "Yes":
                        bucket_name = "eu-samplemanifest"
                        destination = os.path.join(study_name, file_name + file_extension)
                        data = source_file.getvalue()
                        check = upload_data(bucket_name, data, destination)
                        st.markdown(
                            '<p class="medium-font"> {} !!</p>'.format(check),
                            unsafe_allow_html=True)
                        email_ellie(studycode = st.session_state['keepcode'], activity = 'upload')
                    else:
                        st.error("ERROR: Please confirm that the data looks correct on the checkbox above")
                else:
                    st.markdown("ERROR: Please make sure you have given the study name on the leftside panel")
            else:
                st.error("THIS DATASET DOES NOT SEEM TO BE QC. WE HAVE BEEN UNABLE TO CONSIDER IT AS A QC SAMPLE MANIFEST")
                st.error("PLEASE MOVE TO EITHER THE SAMPLE MANIFEST OR THE CLINICAL TAB AND TRY AGAIN AFTER QC")
                st.stop()

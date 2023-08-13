try:
    import os
    from io import BytesIO
    import pandas as pd
    from google.cloud import storage
    import streamlit as st
    from datetime import datetime
    import sys
    sys.path.append('utils')
    from customcss import load_css
    from writeread import upload_data, read_filev2
    from st_aggrid import AgGrid, GridOptionsBuilder
except Exception as e:
    print("Some modules are not installed {}".format(e))

# Setup the GCP Creds
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/secrets/secrets.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/secrets/secrets.json"

def app():
    load_css("/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/apps/css/css.css")
    #load_css("/app/apps/css/css.css")
    st.markdown('<p class="big-font"> GP2 Sample Uploader System</p>', unsafe_allow_html=True)

    # Add study name text box
    study_name = st.sidebar.text_input(
        "Introduce the study name"
    )
    study_name = study_name.strip()
    # Add files browser
    # source_file = st.file_uploader(
    #     "Upload the QC Sample Manifest",
    #     type=["xlsx"]
    # )
    source_file = st.sidebar.file_uploader("Upload the QC Sample Manifest",
                                            type=['xlsx'])

    # Add preview util
    if source_file is not None:
        file_details = {"FileName":source_file.name,
                        "FileType":source_file.type,"FileSize":source_file.size}
        file_name, file_extension = os.path.splitext(file_details["FileName"])
        df, clin, dct = read_filev2(source_file)
        #df[['sample_id', 'clinical_id', 'SampleRepNo']] = df[['sample_id','clinical_id', 'SampleRepNo']].astype(str)
        
        df_builder = GridOptionsBuilder.from_dataframe(df)
        df_builder.configure_grid_options(alwaysShowHorizontalScroll = True,
                                            enableRangeSelection=True, 
                                            pagination=True, 
                                            paginationPageSize=10000,
                                            domLayout='normal')
        godf = df_builder.build()
        AgGrid(df,gridOptions=godf, theme='streamlit', height=400)
        
        clin_builder = GridOptionsBuilder.from_dataframe(clin.iloc[:100,:])
        clin_builder.configure_grid_options(alwaysShowHorizontalScroll = True,
                                            enableRangeSelection=True, 
                                            pagination=True, 
                                            paginationPageSize=10000,
                                            domLayout='normal', height=400)
        clindf = clin_builder.build()
        AgGrid(clin.iloc[:10,:],gridOptions=clindf, theme='streamlit')

        manifest_check = st.selectbox(
            "Does the format look correct",
            ["Yes", "No"]
        )
        # Add uploader button
        if st.button("Upload to GP2 Google Cloud Bucket"):
            try:
                df[['sample_id', 'clinical_id', 'SampleRepNo']] = df[['sample_id','clinical_id', 'SampleRepNo']].astype(str)
                st.write(comp.shape)
                comp = df.compare(st.session_state["smqc"])
                checkdf = True if comp.shape == (0, 0) else False             
            except:
                checkdf = True if df.shape[1] == 33 else False
            
            if checkdf:
                if study_name:
                    if manifest_check == "Yes":
                        bucket_name = "eu-samplemanifest"
                        #destination = os.path.join(study_name, file_name + "_" + get_date() + file_extension)
                        destination = os.path.join(study_name, file_name + file_extension)
                        data = source_file.getvalue()
                        check = upload_data(bucket_name, data, destination)
                        st.markdown(
                            '<p class="medium-font"> {} !!</p>'.format(check),
                            unsafe_allow_html=True)
                    else:
                        st.error("ERROR: Please check the data looks correct and tick the box above")
                else:
                    st.markdown("ERROR: Please make sure you have given the study name")
            else:
                st.error("THIS SAMPLE MANIFEST DOES NOT SEEM TO BE QC. PLEASE MOVE TO THE QC TAB AND TRY AGAIN AFTER QC")
                st.stop()

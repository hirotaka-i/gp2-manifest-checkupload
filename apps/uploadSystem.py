try:
    import os
    from io import BytesIO
    import pandas as pd
    from google.cloud import storage
    import streamlit as st
    from datetime import datetime
except Exception as e:
    print("Some modules are not installed {}".format(e))
    

# Setup the GCP Creds
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/secrets/secrets.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/secrets/secrets.json"

def upload_data(bucket_name, data, destination):
    """Upload a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination)
    blob.upload_from_string(data)
    return "File successfully uploaded to GP2 storage system"

def app():
    st.markdown(
        """
        <style>
        textarea {
            font-family:Arial; font-size: 25px;
        }
        input {
            font-family:Arial; font-size: 25px;
        }
        .big-font {
            font-family:Helvetica; color:#0f557a; font-size:48px !important;
        }
        .medium-font {
            font-family:Arial; color:000000; font-size:18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<p class="big-font"> GP2 Sample Uploader System</p>', unsafe_allow_html=True)

    # Add study name text box
    study_name = st.text_input(
        "Introduce the study name"
    )
    # Add files browser
    source_file = st.file_uploader(
        "Upload the QC Sample Manifest",
        type=["tsv", "csv", "xlsx"]
    )

    # Add preview util
    if source_file is not None:
        file_details = {"FileName":source_file.name,
                        "FileType":source_file.type,"FileSize":source_file.size}
        file_name, file_extension = os.path.splitext(file_details["FileName"])
        
        if file_extension == ".csv":
            df = pd.read_csv(source_file)
        elif file_extension == ".tsv":
            df = pd.read_csv(source_file, sep = '\t')
        elif file_extension == ".xlsx":
            df = pd.read_excel(source_file, sheet_name=0)
        
        # Do minor processing to make sure columnd types of df matches those in st.session_state["dfqc"]
        df[['sample_id', 'clinical_id', 'SampleRepNo']] = df[['sample_id','clinical_id', 'SampleRepNo']].astype(str)
        df = df.reset_index(drop=True)
        
        
        st.dataframe(
            df.head(10).style.set_properties(**{"background-color": "brown", "color": "lawngreen"})
        )
        manifest_check = st.selectbox(
            "Does the format look correct",
            ["Yes", "No"]
        )
        
        # Add uploader button
        if st.button("Upload to GP2 Google Cloud Bucket"):
            checkdf = df.compare(st.session_state["dfqc"])
            if checkdf.shape == (0, 0):
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
                        st.markdown("ERROR: Please make sure you have given the study name")
                else:
                    st.error("ERROR: Please make sure you have given the study name")
            
            else:
                st.error("THIS SAMPLE MANIFEST DOES NOT SEEM TO BE QC. PLEASE MOVE TO THE QC TAB AND TRY AGAIN AFTER QC")
        

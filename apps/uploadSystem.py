try:
    import io
    import os
    from io import BytesIO
    import pandas as pd
    from google.cloud import storage
    import streamlit as st
    from datetime import datetime
except Exception as e:
    print("Some modules are not installed {}".format(e))

# Setup the GCP Creds
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/secrets/secrets.json"

# def get_date():
#     """ Get year month day sample manifest was uploaded """
#     dates = [str(datetime.now().year) , str(datetime.now().month), str(datetime.now().day)]
#     #mydate = 
#     #return(currentMonth, currentYear)
#     return "".join(dates)

def read_manifest(file_extension, source_file):
    """Read the manifest uploaded to the app"""
    if file_extension in [".csv", ".tsv"]:
        data = source_file.getvalue()
    else:
        data = str(source_file.read(), "utf-8")
    return data

# def view_manifest(source_file, file_extension):
#     """Preview uploaded sample manifest"""
#     if file_extension in [".csv", ".tsv"]:
#         bytes_data = source_file.getvalue()
#         data = bytes_data.decode('utf-8').splitlines()
#         st.session_state["preview"] = ''
#         for i in range(0, min(5, len(data))):
#             st.session_state["preview"] += data[i]    
#         preview = st.text_area("DATA PREVIEW", "", height = 150, key = "preview")

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
        type=["tsv","csv"]
    )

    # Add preview util
    if source_file is not None:
        file_details = {"FileName":source_file.name,
                        "FileType":source_file.type,"FileSize":source_file.size}
        file_name, file_extension = os.path.splitext(file_details["FileName"])
        #view_manifest(source_file, file_extension)
        
        if file_extension == ".csv":
            df = pd.read_csv(source_file).head(10)
        elif file_extension == ".tsv":
            df = pd.read_csv(source_file, sep = '\t').head(10)
        else:
            st.error("The self-QC tool generated files in CSV/TSV format only")
            st.error("Please, make sure you are uploading the self-QC sample manifest generated on the QC tab")
            st.stop()
        
        st.dataframe(
            df.style.set_properties(**{"background-color": "brown", "color": "lawngreen"})
        )
        manifest_check = st.selectbox(
        "Does the format look correct",
        ["Yes", "No"]
        )

        # Add uploader button
        if st.button("Upload to GP2 Google Cloud Bucket"):
            if study_name:
                if manifest_check == "Yes":
                    bucket_name = "eu-samplemanifest"
                    #destination = os.path.join(study_name, file_name + "_" + get_date() + file_extension)
                    destination = os.path.join(study_name, file_name + file_extension)
                    data = read_manifest(file_extension, source_file)
                    check = upload_data(bucket_name, data, destination)
                    st.markdown(
                        '<p class="medium-font"> {} !!</p>'.format(check), 
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '<p class="medium-font">Please, go back the QC tab and make sure the manifest meets all criteria</p>', 
                        unsafe_allow_html=True)         
            else:
                st.markdown(
                    '<p class="medium-font">Please make sure you have given the study name </p>', 
                    unsafe_allow_html=True)
    

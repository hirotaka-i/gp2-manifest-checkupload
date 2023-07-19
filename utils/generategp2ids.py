import json
import ijson
import numpy as np
import pandas as pd
from google.cloud import storage
import streamlit as st

@st.cache
def update_masterids(ids_log, ids_dict):
    client = storage.Client()
    bucket = client.get_bucket('eu-samplemanifest')
    blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230718.json')
    
    with blob.open("r") as fp:
        masterids = json.load(fp)
    
    if bool(ids_dict):
        for study, newdata in ids_log.items():
            masterids[study].update(newdata)
    else:
        for study, newdata in ids_log.items():
            masterids[study] = newdata
    
    with blob.open("w") as fp:
        json.dump(masterids, fp)
    
    print("MASTER IDS UPDATED")

@st.cache
def master_key(studies):
    # ACCESS MASTERGP2IDS_JSON IN GP2 BUCKET
    client = storage.Client()
    bucket = client.get_bucket('eu-samplemanifest')
    blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230718.json')
    
    ids_tracker = {}
    with blob.open("r") as f:
        for cohort in studies:
            for record in ijson.items(f, cohort):
                ids_tracker.update({cohort : record})
    
    return(ids_tracker)

# CONVERT THIS INTO A FUNCTIONS
# INPUT
    # uids
    # n
    #df_newids
def getgp2ids(df_updateids, n, uids, study_code):
    mapid = {}
    for uid in uids:
        mapid[uid]= n
        n += 1
    mydf = df_updateids.copy()
    mydf['uid_idx'] = mydf['sample_id'].map(mapid)
    mydf['GP2ID'] = [f'{study_code}_{i:06}' for i in mydf.uid_idx]
    mydf['uid_idx_cumcount'] = mydf.groupby('GP2ID').cumcount() + 1
    mydf['GP2sampleID'] = mydf.GP2ID + '_s' + mydf.uid_idx_cumcount.astype('str')
    mydf['SampleRepNo'] = 's' + mydf.uid_idx_cumcount.astype('str')
    mydf.drop(['uid_idx','uid_idx_cumcount'], axis = 1, inplace = True)
    return(mydf)



# @st.cache
# def blobbucket(bname = 'eu-samplemanifest'):
#     client = storage.Client()
#     bucket = client.get_bucket(bname)
#     blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230718.json')
#     return blob

# @st.cache
# def update_masterids(blob, ids_log, ids_dict):
#     #client = storage.Client()
#     #bucket = client.get_bucket('eu-samplemanifest')
#     #blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230718.json')
#     with blob.open("r") as fp:
#         masterids = json.load(fp)
    
#     #if 'ids_tracker' in globals():
#     if bool(ids_dict):
#         for study, newdata in ids_log.items():
#             masterids[study].update(newdata)
#     else:
#         for study, newdata in ids_log.items():
#             masterids[study] = newdata
    
#     with blob.open("w") as fp:
#         json.dump(masterids, fp)
    
#     print("MASTER IDS UPDATED")

# @st.cache
# def master_key(blob, studies):
#     # ACCESS MASTERGP2IDS_JSON IN GP2 BUCKET
#     #client = storage.Client()
#     #bucket = client.get_bucket('eu-samplemanifest')
#     #blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230718.json')
#     ids_tracker = {}
#     with blob.open("r") as f:
#         for cohort in studies:
#             st.write("IN")
#             for record in ijson.items(f, cohort):
#                 ids_tracker.update({cohort : record})
#     return(ids_tracker)
import json
import ijson
import numpy as np
import pandas as pd
from google.cloud import storage
import streamlit as st


#@st.cache(hash_funcs={'_json.Scanner': hash})
@st.experimental_memo()
def update_masterids(ids_log, ids_dict):
    client = storage.Client()
    bucket = client.get_bucket('eu-samplemanifest')
    #blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230718.json')
    blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230810.json')
    
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
    
    return(masterids)
    #print("MASTER IDS UPDATED")


@st.cache
def master_key(studies):
    # ACCESS MASTERGP2IDS_JSON IN GP2 BUCKET
    client = storage.Client()
    bucket = client.get_bucket('eu-samplemanifest')
    #blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230718.json')
    blob = bucket.blob('IDSTRACKER/CLINICALGP2IDS_MAPPER_20230810.json')
    
    ids_tracker = {}
    with blob.open("r") as f:
        for cohort in studies:
            for record in ijson.items(f, cohort):
                ids_tracker.update({cohort : record})
    
    return(ids_tracker)


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


def assign_unique_gp2clinicalids(df, clinicalid_subset):

    if isinstance(clinicalid_subset, pd.Series):
        clinicalid_subset = clinicalid_subset.to_frame().T

    sampleid = clinicalid_subset.sort_values(by=['master_GP2sampleID'])\
                                .reset_index(drop = True)\
                                .dropna(subset=['master_GP2sampleID'], axis = 0)
    sampleid = sampleid.loc[sampleid.index[-1], 'master_GP2sampleID'].split("_")
    getuniqueid = sampleid[0] + "_" + sampleid[1]
    get_sidrepno = int(sampleid[2].replace("s","")) + 1

    index_modify = clinicalid_subset['index'].unique() #clinicalid_subset[clinicalid_subset['GP2sampleID'].isnull()] #.index
    assign_gp2sampleid = [getuniqueid + "_s" + str(get_sidrepno + i) for i in range(len(index_modify))]
    df.loc[index_modify, 'GP2sampleID'] = assign_gp2sampleid
    getnewidrows = df.loc[index_modify].copy()
    return (getnewidrows)



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
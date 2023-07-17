import ijson
import json
import numpy as np
import pandas as pd
from google.cloud import storage

def update_masterids(blob, ids_log):
    with blob.open("r") as fp:
        masterids = json.load(fp)
    
    if 'ids_tracker' in globals():
        for study, newdata in ids_log.items():
            masterids[study].update(newdata)
    else:
        for study, newdata in ids_log.items():
            masterids[study] = newdata
    
    with blob.open("w") as fp:
        json.dump(masterids, fp)
    
    print("MASTER IDS UPDATED")

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



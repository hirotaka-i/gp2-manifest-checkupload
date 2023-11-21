import streamlit as st
import pandas as pd
import numpy as np

def checkNull(df, voi):
    """
    This will check for null values with a given variable of interest and allow you
    to observe null values within context
    """
    nulls = df[df.loc[:,voi].isnull()]
    n_null = len(nulls)
  
    if n_null==0:
        st.write(f'{len(df)} entries: No null values')
    if n_null>0:
        st.write(f'{len(df)} entries: {n_null} null entries were found')
    #st.dataframe(nulls)
    return(nulls)

def TakeOneEntry(df, key, method='less_na'):
  """
  This function takes the obs with less NAs when duplicated.
  If method=='ffill' foward fill the missingness and take the last entry.
  Do the opposite if method=='bfill'
  """
  if method=='less_na':
    df['n_missing'] = pd.isna(df).sum(axis=1)
    df = df.sort_values(key+['n_missing']).copy()
    df = df.drop_duplicates(subset=key, keep='first')
    df = df.drop(columns=['n_missing']).copy()

  else:
      print('FFILL on process: DO NOT FORGET to sort before using this function!!')
      df.update(df.groupby(key).fillna(method=method))
      df=df.reset_index(drop=True)
      if method=='ffill':
        df = df.drop_duplicates(subset=key, keep='last').copy()
      if method=='bfill':
        df = df.drop_duplicates(subset=key, keep='first').copy()

  return(df)


def checkDup(df, keys):
  """
  This will check the duplicated observations by keys
  Keys should be provided as a list if they are multiple
  e.g. ['PATNO', 'EVENT_ID']
  If there are duplicated observation, returns these obs.
  """
  t = df[keys]
  t_dup = t[t.duplicated()]
  n_dup = len(t_dup)
  if n_dup==0:
    st.write(f'{len(df)} entries: No duplication')
  if n_dup>0:
    d_dup2 = df[df.duplicated(keep=False, subset=keys)].sort_values(keys)
    st.write(f'{len(df)} entries: {len(d_dup2)} duplicated entries are returned')
    return(d_dup2)


def data_naproc(df):
  navals = df.isna().sum().to_dict()
  cleancols = []
  for k, v in navals.items():
      if (v / df.shape[0] > 0.6):
          continue
      cleancols.append(k)
  df = df.fillna(999)
  return(df[cleancols], cleancols)


def detect_multiple_clindups(df):
  st.error(f'There seems to be a problem with this sample manifest')
  groupids = df.groupby(['clinical_id']).size().sort_values(ascending=False)
  groupids_problems = list(groupids[groupids > 3].items())
  for problem_tuple in groupids_problems:
      repid = problem_tuple[0]
      n_reps = problem_tuple[1]
      st.error(f'We have detected a total of {n_reps} repetitions for the clinical id code {repid} ')
      show_problemchunk = df[df.clinical_id == repid][['study','sample_id','clinical_id']]
      st.dataframe(
              show_problemchunk.style.set_properties(**{"background-color": "brown", "color": "lawngreen"})
              )
  st.stop()


def sample_type_fix(df, allowed_samples):
  allowed_samples_strp = [samptype.strip().replace(" ", "") for samptype in allowed_samples]
  
  sampletype = df.sample_type.copy()
  sampletype = sampletype.str.replace(" ", "")
  map_strip_orig = dict(zip(sampletype.unique(), df.sample_type.unique()))
  not_allowed_v2 = list(np.setdiff1d(sampletype.unique(), allowed_samples_strp))
  
  if len(not_allowed_v2)>0:
    st.text('WE have found unknown sample types')
    st.text('Writing entries with sample_type not allowed')
    all_unknwown = []
    for stripval, origval in map_strip_orig.items():
      if stripval in not_allowed_v2:
        all_unknwown.append(origval)
    st.error(f'We could not find the following codes {all_unknwown}') 
    st.error(f'Printing the list of allowed samples types for reference {allowed_samples}')
    st.stop()
  else:
    st.text('We have found some undesired whitespaces in some sample type values')
    st.text('Processing whitespaces found in certain sample_type entries')
    stype_map = dict(zip(allowed_samples_strp, allowed_samples))
    newsampletype = sampletype.replace(stype_map)
    df['sample_type'] = newsampletype
    st.text('sample type count after removing undesired whitespaces')
    st.write(df.sample_type.astype('str').value_counts())

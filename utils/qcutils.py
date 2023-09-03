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

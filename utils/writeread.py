import pandas as pd
import numpy as np
import datetime as dt
from io import BytesIO
import streamlit as st
import xlsxwriter
from google.cloud import storage


def upload_data(bucket_name, data, destination):
    """Upload a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination)
    blob.upload_from_string(data)
    return "File successfully uploaded to GP2 storage system"

def to_excelv2(df,clin, dct):
    """It returns an excel object sheet with the QC sample manifest
    and clinical data written in separate
    """
    today = dt.datetime.today()
    version = f'{today.year}{today.month}{today.day}'
    study_code = df.study.unique()[0]
    ext = "xlsx"
    filename = "{s}_sample_manifest_selfQC_{v}.{e}".format(s=study_code, v = version, e = ext)
    
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='sm')
    clin.to_excel(writer, index=False, sheet_name='clinical')
    dct.to_excel(writer, index=False, sheet_name='Dictionary')
    writer.save()
    processed_data = output.getvalue()
    return processed_data, filename

def to_excel(df, datatype = 'sm'):
    """It returns an excel object sheet with the QC sample manifest
    and clinical data written in separate
    """
    today = dt.datetime.today()
    version = f'{today.year}{today.month}{today.day}'
    study_code = df.study.unique()[0]
    ext = "xlsx"
    if datatype == 'sm':
        filename = "{s}_sample_manifest_selfQC_{v}.{e}".format(s=study_code, v = version, e = ext)
    else:
        filename = "{s}_clinial_data_selfQC_{v}.{e}".format(s=study_code, v = version, e = ext)
    
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='sample_manifest')
    writer.save()
    processed_data = output.getvalue()
    return processed_data, filename




def read_file(data_file):
    if data_file.type == "text/csv":
        df = pd.read_csv(data_file)
    elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(data_file, sheet_name=0)
    return (df)

def read_filev2(data_file):
    #if data_file.type == "text/csv":
        #dfdemo = pd.read_csv(data_file)
    if data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        dfdemo = pd.read_excel(data_file, sheet_name=0)
        dfclin = pd.read_excel(data_file, sheet_name=1)
        try:
            dfdict = pd.read_excel(data_file, sheet_name=2)
        except:
            dfdict = None
    else:
        st.error("Please make sure you upload the temaplate excel file")
        st.stop()
    return (dfdemo, dfclin, dfdict)


# def to_excel(df):
#     """It returns an excel object sheet with the QC sample manifest
#     written in Sheet1
#     """
#     output = BytesIO()
#     writer = pd.ExcelWriter(output, engine='xlsxwriter')
#     df.to_excel(writer, index=False, sheet_name='Sheet1')
#     workbook = writer.book
#     worksheet = writer.sheets['Sheet1']
#     format1 = workbook.add_format({'num_format': '0.00'})
#     writer.save()
#     processed_data = output.getvalue()
#     return processed_data


# def read_file(data_file):
#     if data_file.type == "text/csv":
#         df = pd.read_csv(data_file)
#     elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
#         df = pd.read_excel(data_file, sheet_name=0)
#     return (df)


# def output_create(df, filetype = "CSV"):
#     """It returns a tuple with the file content and the name to
#     write through a download button
#     """
#     today = dt.datetime.today()
#     version = f'{today.year}{today.month}{today.day}'
#     study_code = df.study.unique()[0]

#     if filetype == "CSV":
#         file = df.to_csv(index=False).encode()
#         ext = "csv"
#     elif filetype == "TSV":
#         file = df.to_csv(index=False, sep="\t").encode()
#         ext = "tsv"
#     else:
#         file = to_excel(df)
#         ext = "xlsx"
#     filename = "{s}_sample_manifest_selfQC_{v}.{e}".format(s=study_code, v = version, e = ext)

#     return (file, filename)


# def output_create(df, clin, filetype = "CSV"):
#     """It returns a tuple with the file content and the name to
#     write through a download button
#     """
#     today = dt.datetime.today()
#     version = f'{today.year}{today.month}{today.day}'
#     study_code = df.study.unique()[0]
#     if filetype == "CSV":
#         file = df.to_csv(index=False).encode()
#         ext = "csv"
#     elif filetype == "TSV":
#         file = df.to_csv(index=False, sep="\t").encode()
#         ext = "tsv"
#     else:
#         #file = df.to_excel(df)
#         ext = "xlsx"
#         filename = "{s}_sample_manifest_selfQC_{v}.{e}".format(s=study_code, v = version, e = ext)
#         with pd.ExcelWriter(filename) as file:  
#             df.to_excel(file, sheet_name='demographics')
#             clin.to_excel(file, sheet_name='clinical')
#     return (file, filename)
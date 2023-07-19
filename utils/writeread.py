import pandas as pd
import numpy as np
import datetime as dt
from io import BytesIO
import xlsxwriter
from google.cloud import storage

def read_file(data_file):
    if data_file.type == "text/csv":
        df = pd.read_csv(data_file)
    elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(data_file, sheet_name=0)
    return (df)

def to_excel(df):
    """It returns an excel object sheet with the QC sample manifest
    written in Sheet1
    """
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def output_create(df, filetype = "CSV"):
    """It returns a tuple with the file content and the name to
    write through a download button
    """
    today = dt.datetime.today()
    version = f'{today.year}{today.month}{today.day}'
    study_code = df.study.unique()[0]

    if filetype == "CSV":
        file = df.to_csv(index=False).encode()
        ext = "csv"
    elif filetype == "TSV":
        file = df.to_csv(index=False, sep="\t").encode()
        ext = "tsv"
    else:
        file = to_excel(df)
        ext = "xlsx"
    filename = "{s}_sample_manifest_selfQC_{v}.{e}".format(s=study_code, v = version, e = ext)

    return (file, filename)

def upload_data(bucket_name, data, destination):
    """Upload a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination)
    blob.upload_from_string(data)
    return "File successfully uploaded to GP2 storage system"

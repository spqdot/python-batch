# Hello Shrabani - Yes Amit
from sqlalchemy import create_engine, text
import pandas as pd
import datetime
import streamlit as st
from modules.db import (
    server_con_engine,
    save_to_db
    )

st.set_page_config(layout="wide")

# Page starts here
st.title("Upload and Read Price Sample Data")
st.write("This app allows you to upload CSV or Excel files and read data from SQL Server.")
st.write("Please ensure that the uploaded file has the correct format and columns as required by the database.")

# server_con_engine =  get_connection(st.secrets.SERVER01)

# Upload section for CSV and Excel files
tab1, tab2 = st.tabs(["Upload CSV/Excel", "Read Price Data"])
with tab1:
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            st.write("Preview of uploaded data:")
            st.dataframe(df_upload.head())
            if st.button("Upload to SQL Server", key="upload_btn"):
                with st.spinner('Uploading data to SQL Server...'):
                    # df_upload.to_sql(name='price_data', con=conn, if_exists='append', index=False)
                    save_to_db(df_upload)
                    st.success("Data uploaded successfully to price_data table on sqlserver01.")
        except Exception as e:
            st.error(f"Error uploading file: {e}")

# Query section
with tab2:
    with server_con_engine.begin() as conn:
        # query = st.text_input("Write your query", value="select * from sab.price_data  order by  lastupdated_date desc")
        query = "select * from sab.price_data  order by  lastupdated_date desc"
        if st.button("Read Price Data from SQL Server", key="read_btn"):
            with st.spinner('Reading data from SQL Server...'):
                try:
                    df = pd.read_sql(text(query), conn)
                    st.write("Preview of data from SQL Server:")
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"Error reading data: {e}")

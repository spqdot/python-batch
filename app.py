# Hello Shrabani - Yes Amit
from sqlalchemy import create_engine, text
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

def get_connection(server):
    username = server['USER']
    password = server['PWD']    
    database = server['DATABASE']
    host = server['HOST']
    
    conn_string = f"""mssql+pyodbc://{username}:{password}@{host}/{database}?driver=ODBC+Driver+17+for+SQL+Server"""
    print(conn_string)
    conn_engine=create_engine(conn_string)
    return conn_engine

server_con_engine =  get_connection(st.secrets.SERVER01)

st.title("Upload and Read Price Sample Data")
st.write("This app allows you to upload CSV or Excel files and read data from SQL Server.")
st.write("Please ensure that the uploaded file has the correct format and columns as required by the database.")

def save_data_to_server(df):
    with server_con_engine.begin() as conn:
        df.to_sql(name='price_data_temp', con=conn, if_exists='replace', index=False)

        create_table = """
        if not exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'price_data' and TABLE_SCHEMA = 'sab')
        CREATE TABLE sab.[price_data](
            [SYMBOL] [varchar](max) NULL,
            [SERIES] [varchar](max) NULL,
            [OPEN] [float] NULL,
            [HIGH] [float] NULL,
            [LOW] [float] NULL,
            [CLOSE] [float] NULL,
            [LAST] [float] NULL,
            [PREVCLOSE] [float] NULL,
            [TOTTRDQTY] [bigint] NULL,
            [TOTTRDVAL] [float] NULL,
            [TIMESTAMP] [date] NULL,
            [TOTALTRADES] [bigint] NULL,
            [ISIN] [varchar](max) NULL,
            [TRANSACTION] CHAR(1) NULL,
            [LastUpdated_date] datetime null
        )
        """
        merge_sql = text("""
        MERGE INTO sab.price_data AS target
        USING price_data_temp AS source
        ON (target.ISIN = source.ISIN and target.TIMESTAMP =source.TIMESTAMP and target.SERIES=source.SERIES)
        WHEN MATCHED 
        AND 
            (
                ISNULL(target.[OPEN], 0) <> ISNULL(source.[OPEN],0) OR  
                ISNULL(target.[LOW], 0) <> ISNULL(source.[LOW],0) OR  
                ISNULL(target.[CLOSE], 0) <> ISNULL(source.[CLOSE],0) OR  
                ISNULL(target.[PREVCLOSE], 0) <> ISNULL(source.[PREVCLOSE],0) OR  
                ISNULL(target.[LAST], 0) <> ISNULL(source.[LAST],0) OR  
                ISNULL(target.[TOTTRDQTY], 0) <> ISNULL(source.[TOTTRDQTY],0) OR  
                ISNULL(target.[TOTALTRADES], 0) <> ISNULL(source.[TOTALTRADES],0) OR  
                ISNULL(target.HIGH, 0) <> ISNULL(source.HIGH, 0)
            ) 
        THEN 
            UPDATE SET 
                [OPEN] = source.[OPEN],
                HIGH = source.HIGH,
                LOW = source.LOW,
                [CLOSE] = source.[CLOSE],
                LAST = source.LAST,
                PREVCLOSE = source.PREVCLOSE,
                TOTTRDQTY = source.TOTTRDQTY,
                TOTTRDVAL = source.TOTTRDVAL,       
                TOTALTRADES = source.TOTALTRADES,
                SYMBOL = source.SYMBOL,
                [TRANSACTION] = 'U',
                LastUpdated_date = source.LastUpdated_date
        WHEN NOT MATCHED THEN 
            INSERT (SYMBOL, SERIES, [OPEN], HIGH, LOW, [CLOSE], LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES, ISIN, [TRANSACTION], LastUpdated_date)
            VALUES (source.SYMBOL, source.SERIES, source.[OPEN], source.HIGH, source.LOW, source.[CLOSE], source.LAST, source.PREVCLOSE, source.TOTTRDQTY, source.TOTTRDVAL, source.TIMESTAMP, source.TOTALTRADES, source.ISIN, 'I', LastUpdated_date);
        """)

        conn.execute(text(create_table))
        conn.execute(merge_sql)
        conn.execute(text("drop table if exists price_data_temp"))

        st.write(f"Saving data to database {st.secrets.SERVER01['DATABASE']} ....")

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
                    with server_con_engine.begin() as conn:
                        # df_upload.to_sql(name='price_data', con=conn, if_exists='append', index=False)
                        save_data_to_server(df_upload)
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

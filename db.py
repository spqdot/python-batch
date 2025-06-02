import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

def get_connection(server):

    server_name = server.HOST
    database = server['DATABASE']
    username = server['USER']
    password = server['PWD']
    conn_string = f"""mssql+pyodbc://{username}:{password}@{server_name}/{database}?driver=ODBC+Driver+17+for+SQL+Server"""
    conn_engine=create_engine(conn_string)
    return conn_engine


# local_con_engine =  get_connection(server = st.secrets.LOCAL)
server_con_engine =  get_connection(server = st.secrets.SERVER01)


def save_to_db(df):
    with server_con_engine.begin() as conn:
        df["TIMESTAMP"]= pd.to_datetime(df["TIMESTAMP"])
        df["LastUpdated_date"] = datetime.now()
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
            VALUES (source.SYMBOL, source.SERIES, source.[OPEN], source.HIGH, source.LOW, source.[CLOSE], source.LAST, source.PREVCLOSE, source.TOTTRDQTY, source.TOTTRDVAL, source.TIMESTAMP, source.TOTALTRADES, source.ISIN, 'I', source.LastUpdated_date);
        """)

        conn.execute(text(create_table))
        conn.execute(merge_sql)
        conn.execute(text("drop table if exists price_data_temp"))

        st.write(f"Saving data to database {st.secrets.SERVER01['DATABASE']} ....")
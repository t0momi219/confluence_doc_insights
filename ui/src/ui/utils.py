import os
import base64
from time import sleep

import pandas as pd
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.exceptions import SnowparkSessionException


def create_execute_query():
    """create_execute_query
    クエリ実行用関数 execute_query を作成するクロージャ。

    ### execute_query
    execute_queryは一つのクエリを受け取り、実行します。

    Examples:
        >>> execute_query = create_execute_query()
        >>> execute_query("select * from table where id = ?", params=(1,))
    """
    try:
        # streamlit in snowflakeの内部ならば、snowparkセッションを使ってクエリ実行
        session = get_active_session()
    except SnowparkSessionException as e:
        if not os.path.isfile('.streamlit/secrets.toml'):
            raise e
        secrets = st.secrets["snowflake"]
        connection_parameters = {
            "user": secrets["user"],
            "private_key": base64.b64decode(secrets["private_key"]),
            "account": secrets["account"],
            "warehouse": secrets["warehouse"],
            "database": secrets["database"],
            "schema": secrets["schema"]
        }
        session = Session.builder.configs(connection_parameters).create()
        # streamlit in snowflakeの外部（開発中のローカル環境など）ならば、python-connectorを使ってクエリ実行
    finally:
        def execute_query(query, params=()):
            return session.sql(query, params=params).to_pandas()
        return execute_query

def create_execute_queries():
    """create_execute_queries
    クエリ実行用関数 execute_queries を作成するクロージャ。

    ### execute_queries
    execute_queriesは複数のクエリのリストを受け取り、非同期に実行します。

    Args:
        queries: クエリのリスト。リストの要素は、それぞれクエリ本文とパラメータ辞書を保持したタプルです。

    Returns:
        list: 各クエリの処理結果が格納されたpd.DataFrame。並び順は、投入されたクエリリストの順序に一致。

    Raises:
        リストに含まれるクエリのうち一つでもエラーが起きたら、そのエラーをRaiseします。
    
    Examples:
        >>> execute_queries = create_execute_queries()
        >>> results = execute_queries(
            [
                ("select page_id, name from pages where page_id = ?", (1,)),
                ("select current_datetime()", ())
            ])
        >>> results[0]
            | PAGE_ID | NAME |
            | :------ | :--- |
            | 1       | hoge |
        >>> results[1]
            | CURRENT_DATETIME() |
            | :----------------- |
            | 2024-08-27 00:00:00|
    """
    try:
        # streamlit in snowflakeの内部ならば、snowparkセッションを使ってクエリ実行
        session = get_active_session()    
    except SnowparkSessionException as e:
        # streamlit in snowflakeの外部（開発中のローカル環境など）ならば、python-connectorを使ってクエリ実行
        if not os.path.isfile('.streamlit/secrets.toml'):
            raise e
        secrets = st.secrets["snowflake"]
        connection_parameters = {
            "user": secrets["user"],
            "private_key": base64.b64decode(secrets["private_key"]),
            "account": secrets["account"],
            "warehouse": secrets["warehouse"],
            "database": secrets["database"],
            "schema": secrets["schema"]
        }
        session = Session.builder.configs(connection_parameters).create()
    finally:
        def execute_queries(queries):
            query_ids = []
            for query in queries:
                # すべて非同期に起動する。
                query_id = session.sql(query[0], params=query[1]).collect_nowait().query_id
                query_ids.append(query_id)
            
            # すべてのクエリの完了を待機する
            while not all([session.create_async_job(query_id).is_done() for query_id in query_ids]):
                sleep(0.05)

            # クエリ結果を取り出す。
            results = [session.create_async_job(query_id).result(result_type="pandas") for query_id in query_ids]
            return results
        return execute_queries

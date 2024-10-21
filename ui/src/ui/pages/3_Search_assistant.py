import streamlit as st
import pandas as pd
import numpy as np

from ui.queries import SEARCH_ASSISTANT_QUERY
from ui.utils import create_execute_query


def generate_response(s):
    """回答の生成"""
    execute_query = create_execute_query()
    response_df = execute_query(SEARCH_ASSISTANT_QUERY, [s,s])
    return response_df.iat[0,0]

st.set_page_config(
    layout="wide",
    page_title="検索",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

user_msg = st.chat_input("質問をどうぞ")

if user_msg:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 最新のメッセージを表示
    with st.chat_message("user"):
        st.write(user_msg)

    # アシスタントのメッセージを表示
    response = generate_response(user_msg)
    with st.chat_message("assistant"):
        assistant_response_area = st.empty()
        assistant_response_area.write(response)

    # セッションにチャットログを追加
    st.session_state.messages.append({"role": "user", "content": user_msg})
    st.session_state.messages.append({"role": "assistant", "content": response})

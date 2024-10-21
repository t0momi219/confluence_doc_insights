import streamlit as st
import pandas as pd

from ui.utils import create_execute_query
from ui.queries import ALL_SPACES

@st.cache_data
def get_all_spaces() -> pd.DataFrame:
    """get_all_spaces

    すべてのスペースを取得

    Examples:
        >>> get_all_spaces()
            | SPACE_ID | NAME         |
            | :------- | :----------- |
            | 123456   | sample_space |
    """
    execute_query = create_execute_query()
    return execute_query(ALL_SPACES, [])

def bind():
    """
    サイドバーにスペース選択用のSelectboxを追加する

    これにより、session stateに `space_id` という名前でselectboxで選択されたスペースのspace_idが
    保存されます。
    """
    selected_space_id = st.session_state.space_id if 'space_id' in st.session_state else None

    # スペース一覧を取得
    spaces = get_all_spaces()
    ids = spaces["SPACE_ID"].to_list()
    names = spaces["NAME"].to_list()

    # selectboxをスペース一覧が選択できるように再描画
    space_id = st.sidebar.selectbox(
        "スペースを選択",
        ids,
        key="space_id",
        index=ids.index(selected_space_id) if selected_space_id else 0,
        format_func=lambda id: names[ids.index(id)],
    )

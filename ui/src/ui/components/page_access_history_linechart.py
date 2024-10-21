import streamlit as st
from ui.queries import PAGES_UNIQUE_USER_ACCESS_HISTORY_QUERY
from ui.utils import create_execute_query

@st.cache_data
def get_page_access_history(space_id,page_ids: list):
    """
    対象のページのアクセスユーザ数を取得
    2回目以降はキャッシュから返却する
    """
    # page_ids_strは、SQL内部でPARSE_JSON(TO_JSON(page_ids_str)) にかけられる。
    # これは、バインド変数が配列をサポートしないため。
    # Jsonとして配列の形をした文字列を解析させて、無理やり配列を渡している。
    page_ids_str = f"[{','.join(page_ids)}]"
    execute_query = create_execute_query()
    result = execute_query(PAGES_UNIQUE_USER_ACCESS_HISTORY_QUERY, [space_id, page_ids_str])
    return result

def bind(
    line_chart_placeholder,
    page_ids
):
    """
    各ページを作成日からの経過日別で、ユニークアクセスユーザ数をカウントして線グラフにします
    
    Args:
        line_chart_placeholder: グラフのプレースホルダ
        page_ids: 選択されているページID
    """
    if len(page_ids) == 0:
        line_chart_placeholder.markdown("確認したいページを表から選択してください。")
    else:
        space_id = st.session_state.space_id
        data = get_page_access_history(space_id, page_ids)
        line_chart_placeholder.line_chart(data, x="DATE", y="VIEWERS", color="TITLE")

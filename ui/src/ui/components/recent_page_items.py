from dataclasses import dataclass
from datetime import datetime

import streamlit as st
import pandas as pd

from ui.queries import RECENT_PAGE_ACTIVITY_QUERY, RECENT_PAGE_ACTIVITY_DETAILS_QUERY, LAST_RUN_DATE_QUERY
from ui.models import RecentlyPagesDetailModel, RecentlyPagesSummaryModel
from ui.utils import create_execute_queries

@st.cache_data
def get_queries_result(space_id):
    """
    クエリの実行をする。2回目以降はキャッシュから結果を返却する。
    """
    queries = [
        (RECENT_PAGE_ACTIVITY_QUERY, (space_id, )),
        (RECENT_PAGE_ACTIVITY_DETAILS_QUERY, (space_id, )),
        (LAST_RUN_DATE_QUERY, ())
    ]
    execute_queries = create_execute_queries()
    return execute_queries(queries)

def bind(
    added_pages_metric_placeholder,
    hot_pages_metric_placeholder,
    unreaded_pages_metric_placeholder,
    last_run_date_metric_placeholder,
    page_dataframe_placeholder
):
    """
    1_最近作成されたページのデータを取得し、それぞれの表示領域にバインドする

    Args:
        added_pages_metric_placeholder: 追加されたページのプレースホルダ
        hot_pages_metric_placeholder: 活発なページのプレースホルダ
        unreaded_pages_metric_placeholder: 見逃されたページのプレースホルダ
        last_run_date_metric_placeholder: データ更新日時のプレースホルダ
        page_dataframe_placeholder: データフレーム用のプレースホルダ
    """
    # データの取得
    space_id = st.session_state.space_id
    results = get_queries_result(space_id)

    # 結果をそれぞれ扱いやすいオブジェクトにマップする
    summary = RecentlyPagesSummaryModel.from_df(results[0])
    details = RecentlyPagesDetailModel.from_df(results[1])
    last_run_date = results[2].iat[0,0].strftime('%Y-%m-%d')

    # プレースホルダを要素に置き換え
    added_pages_metric_placeholder.metric("追加されたページ", summary.added_pages, summary.added_pages_delta, help="この期間に作成されたページの総数です。")
    hot_pages_metric_placeholder.metric("活発なページ", summary.hot_pages, summary.hot_pages_delta, help="多くのユーザーが閲覧したページです。")
    unreaded_pages_metric_placeholder.metric("見逃されたページ", summary.unreaded_pages, summary.unreaded_pages_delta, help="最近作成されたにもかかわらず、閲覧者が少ないページです。")
    last_run_date_metric_placeholder.metric("データ更新日時", last_run_date, help="このページのデータが最後に集計された時刻です。")
    event = page_dataframe_placeholder.dataframe(
                    details.table_df,
                    hide_index=True,
                    column_config={
                        "TITLE": "タイトル",
                        "ACTIVITY_CATEGORY": "活動状態",
                        "TOTAL_VIEWS": "総閲覧回数",
                        "AVG_VIEWERS": "平均閲覧ユーザ数",
                        "PATH": "階層",
                        "CREATED_AT": st.column_config.DatetimeColumn(
                            "作成日時",
                            format="YYYY.M.D H:mm:ss"
                        ),
                        "UPDATED_AT": st.column_config.DatetimeColumn(
                            "更新日時",
                            format="YYYY.M.D H:mm:ss"
                        ),
                    },
                    key="recent_page_details_df",
                    on_select="rerun",
                    selection_mode=["multi-row"]
            )

    return details.details_df.iloc[event.selection.rows]["PAGE_ID"].to_list()

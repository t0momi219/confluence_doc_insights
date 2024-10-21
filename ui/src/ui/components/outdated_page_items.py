from dataclasses import dataclass
from typing import List, Tuple
import streamlit as st
import pandas as pd

from ui.queries import LAST_RUN_DATE_QUERY, OUTDATED_PAGE_ACTIVITY_DETAILS_QUERY, OUTDATED_PAGE_ACTIVITY_QUERY
from ui.utils import create_execute_queries

@dataclass
class TabContents:
    page_dataframe_placeholder: st.empty
    line_chart_placeholder: st.empty
    raw_doc_placeholder: st.empty
    review_prompt_template_selectbox_placeholder: st.empty
    review_prompt_textarea_placeholder: st.empty
    review_run_button_placeholder: st.empty
    review_results_placeholder: st.empty

@dataclass
class OutdatedPagesSummary:
    total_pages: int
    hot_pages: int
    unreaded_pages: int
    stable_pages: int
    archived_pages: int
    prev_total_pages: int
    prev_hot_pages: int
    prev_unreaded_pages: int
    prev_stable_pages: int
    prev_archived_pages: int

    @property
    def deltas(self) -> Tuple[int, int, int, int, int]:
        return (
            self.total_pages - self.prev_total_pages,
            self.hot_pages - self.prev_hot_pages,
            self.unreaded_pages - self.prev_unreaded_pages,
            self.stable_pages - self.prev_stable_pages,
            self.archived_pages - self.prev_archived_pages
        )

    @classmethod
    def from_df(cls, df: pd.DataFrame) -> 'OutdatedPagesSummary':
        if len(df) == 0:
            return cls(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        elif len(df) == 1:
            return cls(*(df.iloc[0, 1:6].astype(int).tolist() + [0] * 5))
        elif len(df) == 2:
            return cls(*(df.iloc[1, 1:6].astype(int).tolist() + df.iloc[0, 1:6].astype(int).tolist()))
        else:
            raise ValueError("Unexpected number of rows in dataframe")

@dataclass
class OutdatedPagesDetail:
    details_df: pd.DataFrame
    table_df: pd.DataFrame

    @classmethod
    def from_df(cls, raw_df: pd.DataFrame) -> 'OutdatedPagesDetail':
        details_df = raw_df.sort_values(by=["ACTIVITY_CATEGORY", "PATH"], ascending=[False, True])
        table_df = details_df[["TITLE", "ACTIVITY_CATEGORY", "TOTAL_VIEWS", "AVG_VIEWERS", "PATH", "CREATED_AT", "UPDATED_AT"]]
        return cls(details_df, table_df)

@st.cache_data
def get_queries_result(space_id: str) -> List[pd.DataFrame]:
    queries = [
        (OUTDATED_PAGE_ACTIVITY_QUERY, (space_id,)),
        (LAST_RUN_DATE_QUERY, ()),
        (OUTDATED_PAGE_ACTIVITY_DETAILS_QUERY, (space_id, "活発なページ")),
        (OUTDATED_PAGE_ACTIVITY_DETAILS_QUERY, (space_id, "安定したページ")),
        (OUTDATED_PAGE_ACTIVITY_DETAILS_QUERY, (space_id, "見逃されたページ")),
        (OUTDATED_PAGE_ACTIVITY_DETAILS_QUERY, (space_id, "アーカイブ")),
    ]
    execute_queries = create_execute_queries()
    return execute_queries(queries)

def update_metrics(summary: OutdatedPagesSummary, last_run_date: str, placeholders: dict):
    placeholders['total_pages'].metric("古くなったページ", summary.total_pages, summary.deltas[0], help="この期間に作成されたページの総数です。")
    placeholders['hot_pages'].metric("活発なページ", summary.hot_pages, summary.deltas[1], help="頻繁に更新され、多くのユーザーが閲覧したページです。")
    placeholders['stable_pages'].metric("安定したページ", summary.stable_pages, summary.deltas[3], help="多くのユーザーが閲覧しているものの、更新がしばらく行われていないページです。")
    placeholders['unreaded_pages'].metric("見逃されたページ", summary.unreaded_pages, summary.deltas[2], help="最近更新が行われたにもかかわらず、閲覧者が少ないページです。")
    placeholders['archive_pages'].metric("アーカイブ", summary.archived_pages, summary.deltas[4], help="更新もされず、閲覧者が少ないページです。")
    placeholders['last_run_date'].metric("データ更新日時", last_run_date, help="このページのデータが最後に集計された時刻です。")

def update_tab_content(tab: TabContents, details: OutdatedPagesDetail, key: str):
    event = tab.page_dataframe_placeholder.dataframe(
        details.table_df,
        hide_index=True,
        column_config={
            "TITLE": "タイトル",
            "ACTIVITY_CATEGORY": "活動状態",
            "TOTAL_VIEWS": "総閲覧回数",
            "AVG_VIEWERS": "平均閲覧ユーザ数",
            "PATH": "階層",
            "CREATED_AT": st.column_config.DatetimeColumn("作成日時", format="YYYY.M.D H:mm:ss"),
            "UPDATED_AT": st.column_config.DatetimeColumn("更新日時", format="YYYY.M.D H:mm:ss"),
        },
        on_select="rerun",
        selection_mode=["multi-row"],
        key=f"outdated_page_details_df_{key}"
    )
    
    return details.details_df.iloc[event.selection.rows]["PAGE_ID"].to_list()

def bind(metric_placeholders: dict, tab_contents: dict):
    space_id = st.session_state.space_id
    results = get_queries_result(space_id)

    summary = OutdatedPagesSummary.from_df(results[0])
    last_run_date = results[1].iat[0, 0].strftime('%Y-%m-%d')
    details = [OutdatedPagesDetail.from_df(df) for df in results[2:]]

    update_metrics(summary, last_run_date, metric_placeholders)

    selected_ids_dict = {}
    tab_keys = ['hot_page', 'stable_page', 'unread_page', 'archive_page']
    for tab, detail, key in zip(tab_contents.values(), details, tab_keys):
        selected_ids_dict[key] = update_tab_content(tab, detail, key)

    return selected_ids_dict

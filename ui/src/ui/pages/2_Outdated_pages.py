from collections import namedtuple
from dataclasses import dataclass
import streamlit as st

from ui.components.sidebar import bind as render_sidebar
from ui.components.outdated_page_items import TabContents, bind as render_outdated_page_items
from ui.components.page_access_history_linechart import bind as render_page_access_history_linechart
from ui.components.document_review_items import bind as render_document_review_items

report_window = 14

st.set_page_config(
    layout="wide",
    page_title="古くなったページ",
)

st.markdown(
    "### 古くなったページ",
    help=f"作成から{report_window}日以上経過したページのサマリーです。",
)

#### メトリクスの描画エリア
metric_row = st.container(border=False)
first_row = metric_row.container(border=False)
left_col, right_col = first_row.columns(2)
total_pages_metric_placeholder = left_col.empty()  # 古くなったページ
last_run_date_metric_placeholder = right_col.empty()  # データ更新日時
second_row = metric_row.container(border=False)
subcol1, subcol2, subcol3, subcol4 = second_row.columns(4)
hot_page_metric_placeholder = subcol1.empty()  # 活発なページ
stable_page_metric_placeholder = subcol2.empty()  # 安定したページ
unreaded_pages_metric_placeholder = subcol3.empty()  # 見逃されたページ
archive_pages_metric_placeholder = subcol4.empty()  # アーカイブ

#### タブごとの描画エリア
def build_tab_contents(tab):
    """
    各タブのレイアウト作成
    Args:
        tab (streamlit) : タブエリアのオブジェクト
    Returns:
        TabContents: タブごとに作成されるプレースホルダを管理する名前付きタプル
    """
    tab.markdown("**各ページの詳細**")
    page_dataframe_placeholder = tab.empty()  # データフレーム用のプレースホルダ
    tab.markdown("**ページ毎のユニーク閲覧者数の推移**")
    line_chart_placeholder = tab.empty()  # ラインチャート用のプレースホルダ

    ##### ドキュメントレビューエリア
    review_row = tab.container(border=False)
    review_row.markdown(
        "**ドキュメントレビュー**", help="https://github.com/okld/streamlit-elements"
    )
    left_col, right_col = review_row.columns(2)
    raw_doc_container = left_col.container(border=True)
    raw_doc_placeholder = (
        raw_doc_container.empty()
    )  # 選択したページの内容を表示するエリアのプレースホルダ

    review_prompt_template_selectbox_placeholder = (
        right_col.empty()
    )  # レビュープロンプトのテンプレ選択用selectbox
    review_prompt_textarea_placeholder = (
        right_col.empty()
    )  # レビュープロンプト編集のテキストエリア
    review_run_button_placeholder = right_col.empty()  # レビュー実行ボタン
    review_results_placeholder = right_col.empty()  # レビュー結果の表示エリア

    return TabContents(
        page_dataframe_placeholder,
        line_chart_placeholder,
        raw_doc_placeholder,
        review_prompt_template_selectbox_placeholder,
        review_prompt_textarea_placeholder,
        review_run_button_placeholder,
        review_results_placeholder,
    )

tab_row = st.container(border=False)
tab1, tab2, tab3, tab4 = tab_row.tabs(["活発なページ", "安定したページ", "見逃されたページ", "アーカイブ"])
hot_page_tab = build_tab_contents(tab1)
stable_page_tab = build_tab_contents(tab2)
unread_page_tab = build_tab_contents(tab3)
archive_page_tab = build_tab_contents(tab4)


# データ取得と描画
render_sidebar()
placeholders = {
        'total_pages': total_pages_metric_placeholder,
        'hot_pages': hot_page_metric_placeholder,
        'unreaded_pages': unreaded_pages_metric_placeholder,
        'stable_pages': stable_page_metric_placeholder,
        'archive_pages': archive_pages_metric_placeholder,
        'last_run_date': last_run_date_metric_placeholder,
    }
tabs = {
        'hot_page': hot_page_tab,
        'stable_page': stable_page_tab,
        'unread_page': unread_page_tab,
        'archive_page': archive_page_tab
    }
selected_ids_dict = render_outdated_page_items(
    placeholders,
    tabs
)

for key, selected_ids in selected_ids_dict.items():
    render_page_access_history_linechart(
        tabs[key].line_chart_placeholder,
        selected_ids
    )
    render_document_review_items(
        tabs[key].raw_doc_placeholder,
        tabs[key].review_prompt_template_selectbox_placeholder,
        f"review_prompt_template_selectbox_{key}",
        tabs[key].review_prompt_textarea_placeholder,
        f"review_prompt_textarea_{key}",
        tabs[key].review_run_button_placeholder,
        f"review_run_button_{key}",
        tabs[key].review_results_placeholder,
        selected_ids
    )

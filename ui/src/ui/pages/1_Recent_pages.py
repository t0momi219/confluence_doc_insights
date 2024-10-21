import streamlit as st

from ui.components.sidebar import bind as render_sidebar
from ui.components.recent_page_items import bind as render_recent_page_items
from ui.components.page_access_history_linechart import bind as render_page_access_history_linechart
from ui.components.document_review_items import bind as render_document_review_items

report_window = 14

st.set_page_config(
    layout="wide",
    page_title="最近作成されたページ",
)

st.markdown("### 最近追加されたページ", help=f"過去{report_window}日以内に新規作成されたページのサマリーです。")

##### メトリクスエリア
metric_row = st.container(border=False)
left_col, right_col = metric_row.columns(2)
added_pages_metric_placeholder = left_col.empty() # 追加されたページのプレースホルダ
col1, col2 = left_col.columns(2)
hot_pages_metric_placeholder = col1.empty() # 活発なページのプレースホルダ
unreaded_pages_metric_placeholder = col2.empty() # 見逃されたページのプレースホルダ
last_run_date_metric_placeholder = right_col.empty() # データ更新日時のプレースホルダ

##### 各ページの詳細エリア
details_row = st.container(border=False)
details_row.markdown("**各ページの詳細**")
page_dataframe_placeholder = details_row.empty() # データフレーム用のプレースホルダ
details_row.markdown("**ページ毎のユニーク閲覧者数の推移**")
line_chart_placeholder = details_row.empty() # ラインチャート用のプレースホルダ

##### ドキュメントレビューエリア
review_row = st.container(border=False)
review_row.markdown("**ドキュメントレビュー**", help="https://github.com/okld/streamlit-elements")
left_col, right_col = review_row.columns(2)
raw_doc_container = left_col.container(border=True)
raw_doc_placeholder = raw_doc_container.empty() # 選択したページの内容を表示するエリアのプレースホルダ

review_prompt_template_selectbox_placeholder = right_col.empty() # レビュープロンプトのテンプレ選択用selectbox
review_prompt_textarea_placeholder = right_col.empty() # レビュープロンプト編集のテキストエリア
review_run_button_placeholder = right_col.empty() # レビュー実行ボタン
review_results_placeholder = right_col.empty() # レビュー結果の表示エリア

# データ取得とレンダリング
render_sidebar()
selected_page_ids = render_recent_page_items(
    added_pages_metric_placeholder,
    hot_pages_metric_placeholder,
    unreaded_pages_metric_placeholder,
    last_run_date_metric_placeholder,
    page_dataframe_placeholder
)
render_page_access_history_linechart(
    line_chart_placeholder,
    selected_page_ids
)
render_document_review_items(
    raw_doc_placeholder,
    review_prompt_template_selectbox_placeholder,
    "review_prompt_template_selectbox",
    review_prompt_textarea_placeholder,
    "review_prompt_textarea",
    review_run_button_placeholder,
    "review_run_button",
    review_results_placeholder,
    selected_page_ids
)

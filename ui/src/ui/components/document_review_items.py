from pathlib import Path

import streamlit as st
from ui.queries import PAGE_MD_CONTENTS_QUERY, REVIEW_QUERY
from ui.utils import create_execute_query

TEMPLATES = {
    "レビュー用プロンプト": """
以下の5つの観点で、ドキュメントをレビューしてください。

### 1. 機能品質と構造品質のレビュー
機能品質と構造品質をレビューしてください。具体的には、読者のニーズを満たしているか、目的が明確であるか、情報が正確で完全かを確認してください。また、文章が明確で簡潔で一貫しているかも評価してください。
### 2. アクセシビリティと最新性の確認
アクセシビリティと最新性を確認してください。ユーザーが必要な情報にすぐにアクセスできるか、情報が最新で信頼できるかをチェックしてください。
### 3. ユーザーエクスペリエンスの改善点の特定
ドキュメントをレビューし、ユーザーエクスペリエンスの改善が必要な箇所を特定してください。特に、情報が見つけにくい、理解しにくい、または誤解を招く部分があるかどうかを重点的に確認してください。
### 4. 不必要な情報やデッドリンクの確認
ドキュメントの中で、不必要な情報やデッドリンクが含まれていないか確認してください。また、情報が古くなっている箇所がないかも併せてレビューしてください。
### 5. ドキュメントの有効性評価
ドキュメントが想定読者にとって有効であるかどうかを評価してください。具体的には、読者が求める情報が含まれているか、内容が実際のニーズに合致しているかを確認してください。

# ドキュメント
{{ document }}

"""
}

@st.cache_data
def get_md_contents(page_id):
    """
    ページの本文（マークダウン）の取得
    """
    execute_query = create_execute_query()
    df = execute_query(PAGE_MD_CONTENTS_QUERY, [page_id])
    return df

def build_prompt(prompt, md_contents):
    return prompt.replace("{{ document }}", md_contents)

@st.cache_data
def get_review_result(prompt):
    """
    レビューの実行
    """
    execute_query = create_execute_query()
    df = execute_query(REVIEW_QUERY, [prompt])
    return df

def bind(
    raw_doc_placeholder,
    review_prompt_template_selectbox_placeholder,
    review_prompt_template_selectbox_key,
    review_prompt_textarea_placeholder,
    review_prompt_textarea_key,
    review_run_button_placeholder,
    review_run_button_key,
    review_results_placeholder,
    selected_page_ids,
):
    # レビュープロンプトの選択と編集
    option = review_prompt_template_selectbox_placeholder.selectbox(
        "レビュープロンプトのテンプレートを選択",
        TEMPLATES.keys(),
        key=review_prompt_template_selectbox_key
    )
    prompt = review_prompt_textarea_placeholder.text_area(
        "プロンプト",
        TEMPLATES[option],
        key=review_prompt_textarea_key
    )

    # レビュー対象ドキュメントの取得
    if len(selected_page_ids) != 1:
        raw_doc_placeholder.markdown("レビュー対象となるドキュメントを1件だけ選択して下さい。")
    else:
        md_contents_df = get_md_contents(selected_page_ids[0])
        raw_doc_placeholder.markdown(md_contents_df.iat[0,0])

    # レビューの実行と結果の出力
    if review_run_button_placeholder.button("レビュー実行", key=review_run_button_key):
        if len(selected_page_ids) == 1:
            final_prompt = build_prompt(prompt, md_contents_df.iat[0,0])
            result_df = get_review_result(final_prompt)
            review_results_placeholder.markdown(result_df.iat[0,0])

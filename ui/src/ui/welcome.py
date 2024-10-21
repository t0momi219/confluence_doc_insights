import streamlit as st

from ui.components.sidebar import bind as render_sidebar

st.set_page_config(
    layout="wide",
    page_title="Confluence Docs Insight",
)

st.markdown("# Welcome to Confluence Docs Insight! 👋")

st.markdown("""
Confluenceのスペース上に作成されたドキュメントの状態を確認しましょう。

##### スペースの選択
サイドバーにあるセレクトボックスから確認したいスペースを選択してください。            

##### サブページについて
- 最近作成されたページ（Recent Pages）
    - 直近で作成されたページの分析レポートです。
- 古くなったページ（Outdated Pages）
    - 作成からしばらく経過しているページの分析レポートです。          
- 検索アシスタント（Search Assistant）
    - ロードされたページ情報をもとにしたチャットボットアプリケーションです。
""")

render_sidebar()

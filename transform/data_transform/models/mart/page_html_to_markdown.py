import re
from bs4 import BeautifulSoup, NavigableString

from snowflake.snowpark.types import StringType, VariantType
from snowflake.snowpark.functions import udf, current_timestamp


def model(dbt, session):
    """ページのHTMLのマークダウン化
    
    最後にこのモデルが実行された日以降に更新日付がついているページだけを対象にして、
    delete&insertで更新する。
    """
    dbt.config(
        materialized = "incremental",
        incremental_strategy = "delete+insert",
        unique_key = "page_id",
        packages = ["snowflake-snowpark-python", "beautifulsoup4"]
    )

    # テーブルの読み出し
    page_df = dbt.ref("cleansed_pages")
    if dbt.is_incremental:
        max_from_this = f"select max(updated_at) from {dbt.this}"
        page_df = page_df.filter(page_df.updated_at >= session.sql(max_from_this).collect()[0][0])

    # マークダウン化とチャンク分割のための関数定義
    # FIXME:
    # これらの関数をmodelの外に出そうとするとエラーになる。
    # おそらくhtml_to_markdownでbs4をつかうのに、model関数の外部だとbs4が参照できなくなるせいなのだが、
    # udfの定義でpackagesを追加したり、add_packages関数を呼ぶなりしてセッションにパッケージを紐づけようとしてもうまくいかず、、、
    # 泣く泣くmodelの内部関数にして対応。。。テスタビリティが低いので、いつか直したい。
    # - 発生したエラー： No module named 'main_modules'
    # - 関連してそうなissue： https://discourse.getdbt.com/t/creating-udf-in-dbt-python-models-with-snowflake-as-database/8464
    def html_to_markdown(html):
        """
        html文書をmarkdownにします。
        マークダウンのチャンク化も同時に行います。
        
        #### markdown変換仕様
        1. script, styleなどのタグや、コンフル固有のタグ(ac)を削除します。
        2. よくみられるタグを処理します。
            - 見出し
            - リンク
            - 太字
            - 斜体
            - リスト（箇条書きと連番）
            - コードブロック
        3. 余計な空白を削除します。
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 不要なタグの削除
        # 対象は、<script>, <style>, <ac:*>(Atlassian Confluenceの独自タグ)
        for script in soup(["script", "style", "ac"]):
            script.decompose()
        
        # hタグの置換
        # 例：
        #   <h1>タイトル</h1>
        #   ↓
        #   # タイトル
        # 
        # NOTE:
        # 置換は、ヘッダー コンテンツの前にMarkdownヘッダー構文を挿入し、ヘッダー タグをアンラップする形で行います。
        # 対象文字列の置換での実装は、同じ文字列が本文中に存在する場合でも同様に変換してしまうので、やめてください。
        # 悪い例：
        #   <h1>設計</h1>
        #   <p>本ページは、設計についての記述です。</p>
        #   ↓
        #   # 設計
        #   本ページは、
        # 　# 設計
        # 　についての記述です。
        for i in range(6, 0, -1):
            for header in soup.find_all(f'h{i}'):
                header.insert_before("\n\n"+NavigableString(f"{'#' * i} "))
                header.insert_after("\n\n")
                header.unwrap()
        
        # Aタグの置換
        for link in soup.find_all('a'):
            link.replace_with(f"[{link.get_text()}]({link.get('href')})")
        
        # strongタグ, bタグの置換
        for bold in soup.find_all(['strong', 'b']):
            bold.replace_with(f"**{bold.get_text()}**")
        
        # emタグ、iタグの置換
        for italic in soup.find_all(['em', 'i']):
            italic.replace_with(f"*{italic.get_text()}*")
        
        # 箇条書きの置換
        for ul in soup.find_all('ul'):
            for li in ul.find_all('li'):
                li.replace_with(f"\n- {li.get_text()}\n")
            ul.unwrap()
        
        # 箇条書きの置換
        for ol in soup.find_all('ol'):
            for i, li in enumerate(ol.find_all('li'), 1):
                li.replace_with(f"\n{i}. {li.get_text()}\n")
            ol.unwrap()
        
        # コードブロックの置換
        for code in soup.find_all('code'):
            code.replace_with(f"`{code.get_text()}`")
        
        # 余計なスペースの削除
        text = soup.get_text()
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text

    def __is_blank_or_none(string):
        """
        空白文字のみ、改行文字のみ、Noneの文字列を判定する。
        """
        # Noneの場合
        if string is None or string == 'none':
            return True
        # 空白のみまたは改行のみの場合
        if isinstance(string, str) and string.strip() == '':
            return True
        return False

    def chunking(md_contents, level=1, CHUNK_SIZE=1000):
        """チャンキング
        SnowflakeのVector Embedding関数（EMBED_TEXT_768、EMBED_TEXT_1024）が受け取れるトークン数の上限は512であるため、
        1トークンが日本語の2~4文字に相当すると仮定して、1,000~2,000文字程度の文章しかベクトル化ができない。

        そこで、今回は以下のように文書をチャンクに分割する。
        - ページ全体の文字数を取得する。もし、1,000文字以内ならば、チャンクに区切らない。
        - 1,000文字を超える場合は、h1タグ区切りで文書を分割する。もしh1タグ単位で分割しても1,000文字を超える場合は、h2タグで分割する。
        - これを繰り返して、もしh5タグで分割をしても1,000を超えてしまうのならば、残りを適当に1,000文字づつでパラグラフを切る。
        """
        results = []
        if len(md_contents) <= CHUNK_SIZE:
            # チャンクサイズ以下の長さなら、そのまま
            results.extend([md_contents])
        elif level <= 5:
            # 分割するヘッダーレベルが5を超えていないなら、ヘッダごとに分割する。
            # パターン：改行コードに続いて、#が指定された回数だけ連続し、一つの半角スペースの後に任意の文字列が続いて改行で終わる。
            # NOTE:
            # Pythonでは、以下のreplaceを、level変数をf文字列として直接中に書くこともできるはずだが、
            # dbtモデルでは二重波括弧がJinjaとして解釈されてしまいエラーになる。なのであえてのreplace。
            pattern_str = r'\n+#{level_keyword}\s.*?(?=\n|$)'.replace('level_keyword', str(level))
            pattern = re.compile(pattern_str)
            chunks = pattern.split(md_contents)
            for chunk in chunks:
                results.extend(chunking(chunk, level+1))
        else:
            # 分割時のレベルが5を超えていたら（#### のブロック単体でCHUNK_SIZEを超えてしまっていれば）、単純に文字長で切る
            results.extend([md_contents[i: i+CHUNK_SIZE] for i in range(0, len(md_contents), CHUNK_SIZE)])

        # 空白行で始まっていると、中身がないチャンクができてしまうことがある。
        # 空白文字のみ、改行文字のみ、Noneのチャンクがあれば消す。
        filtered_results = list(filter(lambda x: not __is_blank_or_none(x), results))

        return filtered_results

    # python関数のudf化
    h2m = udf(html_to_markdown, return_type=StringType(), input_types=[StringType()], name="h2m")
    m2c = udf(chunking, return_type=VariantType(), input_types=[StringType()], name="m2c")

    # UDFをそれぞれの列にApply
    page_df = page_df.with_column('MD_CONTENTS', h2m("HTML_CONTENTS"))
    page_df = page_df.with_column('CHUNKED_CONTENTS', m2c("MD_CONTENTS"))
    page_df = page_df.with_column('UPDATED_AT', current_timestamp())
    result = page_df.select("PAGE_ID", "MD_CONTENTS", "CHUNKED_CONTENTS", "UPDATED_AT")

    return result

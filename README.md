# confluence-docs-insight

Atlassian ConfluenceのスペースにあるドキュメントをSnowflakeで可視化する一連のパイプラインと画面を構築します。

# 使い方

本リポジトリをフォークして利用してください。

## 1. Confluenceからのデータロード

dlt(data load tool)を使用して、Confluenceからスペースの内容を読み取り、Snowflakeへロードします。
このリポジトリでは、confluence用のdlt sourceを提供します。

### pipelineの作成

confluence sourceを使ってSnowflakeにスペースの情報をロードするには、以下のようなパイプラインを作成します。

```python
import os
import dlt
from load.confluence import confluence


pipeline = dlt.pipeline(
    pipeline_name="confluence",
    destination="snowflake",
    dataset_name="confluence",
)
data = confluence(
    target_spaces=[],
    analytics_backfill_days=0
)
result = pipeline.run(data)

```

confluence sourceの引数には、以下を取ることができます。

| argument                | description                               |
| :---------------------- | :---------------------------------------- |
| target_spaces           | 収集する対象となるConfluenceスペースの名前のリストです。空の場合、すべてのスペースを取得します。|
| analytics_backfill_days | ページの閲覧数、ユニーク閲覧ユーザ数を取得する対象日付を、今日日付から何日まえまで遡って収集するのかを決定します。|

### ジョブの起動

Github Actionを用いてジョブを起動する例を以下に示します。

```yml
name: Nightly DLT Pipeline

on:
  schedule:
    - cron: '0 16 * * *' # Run at midnight UTC every day

#   即時実行させたい時はコメントインしてコミットしてください。
#   push:
#     branches:
#       - main

jobs:
  run-dlt-pipeline:
    runs-on: ubuntu-latest

    steps:
    - name: Check out repository
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11.6' # Specify the Python version you need
        cache: 'pip' # caching pip dependencies

    - name: Install dependencies
      run: |
        sed '/-e/d' requirements.lock > requirements.txt
        pip install -r requirements.txt

    - name: Run DLT pipeline
      run: |
        python ./src/pipeline.py
      env:
        CREDENTIALS__CONFLUENCE_BASE_URL: ${{ secrets.CONFLUENCE_BASE_URL }}
        CREDENTIALS__CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }}
        CREDENTIALS__CONFLUENCE_API_TOKEN: ${{ secrets.CONFLUENCE_API_TOKEN }}
        CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE: ${{ secrets.SNOWFLAKE_DATABASE }}
        CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME: ${{ secrets.SNOWFLAKE_USERNAME }}
        CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__HOST: ${{ secrets.SNOWFLAKE_ACCOUNT }}
        CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__PRIVATE_KEY: ${{ secrets.SNOWFLAKE_PRIVATE_KEY }}
      working-directory: ./load
```

パイプライン実行時には、環境変数として以下を設定する必要があります。
| キー | 設定する値 | 例 |
| :-- | :-- | :-- |
| CREDENTIALS__CONFLUENCE_BASE_URL | コンフルエンスのURLです。 | https://<your_tenant>.atlassian.net/ |
| CREDENTIALS__CONFLUENCE_USERNAME | コンフルエンスにアクセスするユーザ名です。| |
| CREDENTIALS__CONFLUENCE_API_TOKEN | コンフルエンスにアクセスするためのアクセストークンです。詳しくは[公式ページ](https://ja.confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html)を参照してください。| |
| CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE | ロード先Snowflakeデータベース名です。| |
| CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME | Snowflakeにアクセスするためのユーザ名です。| |
| CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE | Snowflakeにアクセスするロール名です。| |
| CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__HOST | Snowflakeのアカウント識別子です。| xx12345.ap-northeast-1.aws |
| CONFLUENCE__DESTINATION__SNOWFLAKE__CREDENTIALS__PRIVATE_KEY | Snowflakeアクセスユーザのためのキーペア認証用秘密鍵です。| |

> [!CAUTION]
> 絶対に機密情報を直接Gitにコミットしないでください。[シークレット](https://docs.github.com/ja/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)を使用してください。

パイプラインの実行により、Snowflakeの指定したデータベース上に以下の構造が作られることがわかるはずです。

| テーブル名 | 内容 |
| :-- | :-- |
| PAGES | Confluenceからロードしたページの情報です。 |
| SPACES | Confluenceからロードしたスペースの情報です。 |
| VIEWERS | ページの1日あたりユニークな閲覧ユーザー数です。 |
| VIEWS | ページの1日あたり閲覧回数です。 |
| _DLT_LOADS | dltによって生成されるテーブル。 |
| _DLT_PIPELINE_STATE | dltによって生成されるテーブル。 |
| _DLT_VERSION | dltによって生成されるテーブル。 |

## 2. dbtによるデータ加工

ロードしたデータを、dbtで加工し、可視化の準備をします。

まずは以下の環境変数を設定してください。

```bash
export DBT__REPORT_WINDOW=14 # 任意
export DBT__UNIQUE_VIEWS_THRESHOLD=3 # 任意
export DATABASE=<ロード先に指定したDB>
export SCHEMA=CONFLUENCE
export ACCOUNT=<アカウント識別>
export PRIVATE_KEY_PATH=<Snowflakeへの接続のためのキーペアの秘密鍵へのパス>
export USER=<Snowflakeログインユーザ名>
export WAREHOUSE=<利用するウェアハウス>
```

| キー | 設定値 | デフォルト値 |
| :-- | :--- | :--- |
| DBT__REPORT_WINDOW | 最近古くなったページと古くなったページを分ける基準となる日数です。ページの作成日がこの設定した日数以上に経過しているページを、古くなったページとして扱います。| 14日 |
| DBT__UNIQUE_VIEWS_THRESHOLD | 人気のページとそうでないページを分ける基準です。ページのユニーク閲覧者数がこの設定した数以上に多いページを人気のページとして扱います。| 設定されていない場合、デフォルトで収集したすべてのページのユニーク閲覧者数の平均を使って判定するようにします。 | 

環境変数の設定後、以下でdbtを実行します。

```bash
dbt build
```

## 3. Streamlitによる可視化

Streamlit in Snowflakeでダッシュボードをデプロイして、データの可視化を行います。
SnowCLIを使って、デプロイを行います。

Streamlitから実行されるクエリの宛先になるDB、Schemaを変更してください。
ui/src/ui/queries.pyの以下行です。


編集後、以下のコマンドでデプロイを行なってください。
```
snow streamlit deploy -c sandbox --database <DB名> --schema <スキーマ名> --replace
```

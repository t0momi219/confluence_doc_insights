# load

ConfluenceからSnowflakeへページデータを取り込むためのパイプラインです。

## Test

```bash
# 単体テスト
pytest -m unit
# または
rye test -- -m unit

# 結合テスト
source .env # 環境変数からテスト環境の情報を入力
pytest -m integration
# または
rye test -- -m integration
```

from dataclasses import dataclass

import pandas as pd

@dataclass
class RecentlyPagesSummaryModel:
    added_pages: int
    hot_pages: int
    unreaded_pages: int
    prev_added_pages: int
    prev_hot_pages: int
    prev_unreaded_pages: int

    @property
    def added_pages_delta(self):
        return self.added_pages - self.prev_added_pages

    @property
    def hot_pages_delta(self):
        return self.hot_pages - self.prev_hot_pages

    @property
    def unreaded_pages_delta(self):
        return self.unreaded_pages - self.prev_unreaded_pages

    @classmethod
    def from_df(cls, df):
        """
        RECENT_PAGE_ACTIVITY_QUERY の結果からサマリーを計算する

        Examples:
            >>> df
                | agg_target_date | added_pages | hot_pages | unreaded_pages |
                | :-------------- | :---------- | :-------- | :------------- |
                | 2024-07-01      |           1 |         2 |              3 |
                | 2024-07-02      |           4 |         5 |              6 |
            >>> result = RecentlyPagesSummaryModel.from_df(df)
                # ▼こうなる
                # RecentlyPagesSummaryModel(
                #     added_pages=1
                #     hot_pages=2
                #     unreaded_pages=3
                #     prev_added_pages=4
                #     prev_hot_pages=5
                #     prev_unreaded_pages=6
                # )
        """
        if len(df) == 0:
            # データが1件も返らなければ0件とする
            return cls(0,0,0,0,0,0)
        elif len(df) == 1:
            # 1日分しかデータが返らなければ、prevを0とする
            return cls(int(df.iat[0,1]), int(df.iat[0,2]), int(df.iat[0,3]), 0, 0, 0)
        elif len(df) == 2:
            # 2日データが返れば、それぞれの値を設定する
            return cls(int(df.iat[1,1]), int(df.iat[1,2]), int(df.iat[1,3]), int(df.iat[0,1]), int(df.iat[0,2]), int(df.iat[0,3]))
        else:
            raise Exception("内部エラー：最近作成されたページの取得で予想外のエラーが発生しました。")

@dataclass
class RecentlyPagesDetailModel:
    details_df: pd.DataFrame # SQL叩いて取れた生データ
    table_df: pd.DataFrame # 画面に表示する列だけを抽出したテーブル

    @classmethod
    def from_df(cls, raw_df):
        # テーブルを画面に表示するとき、並び順を「活動状態」「階層」ごとにしたい。
        # チェックボックスによるテーブルの選択は、その並び順の行番で管理される（3行目を選択したら、"2"がeventオブジェクトからとれる）。
        # よって、生データと画面表示用のデータが、同じ並び順になっていてほしい。
        # details_dfの時点でソートを行い、table_dfで列を絞るようにした。
        details_df = raw_df.sort_values(by=["ACTIVITY_CATEGORY", "PATH"], ascending=[False, True])
        table_df = details_df[["TITLE", "ACTIVITY_CATEGORY", "TOTAL_VIEWS", "AVG_VIEWERS", "PATH", "CREATED_AT", "UPDATED_AT"]]
        return cls(details_df, table_df)

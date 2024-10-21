from datetime import datetime, timedelta
from itertools import product

from zoneinfo import ZoneInfo, available_timezones

import dlt

from load.clients import v1_client, v2_client

def get_date_range(days_num: int, tz_name: str = 'UTC') -> list:
    """
    指定された日数とタイムゾーンに応じて、今日の日付から遡って日付のリストを作成する。

    Args:
        days_num (int): 遡る日数
        tz_name (str): タイムゾーン名（デフォルトは 'UTC'）

    Returns:
        list: YYYY-MM-DD 形式の日付文字列のリスト

    Examples:
        >>> get_date_range(1, 'America/New_York')
            [{'date': '2024-07-31'}, {'date': '2024-07-30'}]
    """
    try:
        if tz_name not in available_timezones():
            raise ValueError(f"Invalid timezone: {tz_name}")
        tz = ZoneInfo(tz_name)
    except Exception as e:
        print(f"Warning: {e}. Using UTC instead.")
        tz = ZoneInfo('UTC')

    now = datetime.now(tz)
    today = now.date()
    results = [{"date": (today - timedelta(days=i)).strftime('%Y-%m-%d')} for i in range(days_num + 1)]
    return results

@dlt.source
def confluence(target_spaces: list[str],analytics_backfill_days: int,) -> list:
    """Confluence

    a dlt source that loads Atlassian Confluence space, page and analytics data.
    Available resources: [spaces, pages, views, viewers]

    Args:
        target_spaces (list[str]): name of the target spaces. If empty, all spaces will be collected.
        analytics_backfill_days (int): the number of days to backfill views and viewers.
    """

    @dlt.resource(name="spaces", write_disposition="replace")
    def get_spaces():
        """get_spaces

        https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-space/#api-spaces-get
        """
        if len(target_spaces) > 0:
            for space_name in target_spaces:
                for page in v2_client.paginate(f"/spaces?keys={space_name}"):
                    yield page
        else:
            for page in v2_client.paginate("/spaces"):
                yield page

    @dlt.transformer(name="pages", data_from=get_spaces, write_disposition="replace")
    def get_pages(space_list):
        """get_pages

        https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/#api-spaces-id-pages-get
        """
        for space_item in space_list:
            for page in v2_client.paginate(f"/spaces/{space_item['id']}/pages", params={"body-format": "storage"}):
                yield page

    @dlt.transformer(data_from=get_pages, write_disposition="replace")
    def __get_pages_cross_join_date_range(page_list):
        """__get_pages_cross_join_date_range
        
        For backfilling, perform a cross join between pages and dates.
        This function is not exposed as a closure because it does not need to be stored in a table.
        """
        page_id_dict_list = [{"id": page["id"]} for page in page_list]
        date_range = get_date_range(analytics_backfill_days)
        result = [dict(**d1, **d2) for d1, d2 in product(page_id_dict_list, date_range)]
        for item in result:
            yield item

    @dlt.resource(name="views", data_from=__get_pages_cross_join_date_range, write_disposition="append")
    def get_views(page_date_item):
        views = v1_client.get(
                f"/analytics/content/{page_date_item['id']}/views?fromDate={page_date_item['date']}"
            ).json()
        return {"page_id": page_date_item["id"], "date": page_date_item["date"], "views": views["count"]}

    @dlt.resource(name="viewers", data_from=__get_pages_cross_join_date_range, write_disposition="append")
    def get_viewers(page_date_item):
        viewers = v1_client.get(
                f"/analytics/content/{page_date_item['id']}/viewers?fromDate={page_date_item['date']}"
            ).json()
        return {"page_id": page_date_item["id"], "date": page_date_item["date"], "viewers": viewers["count"]}

    return [
        get_spaces,
        get_pages,
        get_views,
        get_viewers
    ]

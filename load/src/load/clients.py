from urllib.parse import urljoin
import dlt

from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import HttpBasicAuth

from requests import Response, Request
from dlt.common import jsonpath

from dlt.sources.helpers.rest_client.paginators import BaseReferencePaginator

class ConfluenceV2CursorPagenator(BaseReferencePaginator):
    """ConfluenceV2CursorPagenator

    カーソルベースのページネーターを使用するConfluence REST API v2用のページネーターです。

    Confluence REST API v2では、カーソルベースのページネーションが使用されます。レスポンスは以下のようになります

        {
            "_links": {
                "next": "/wiki/api/v2/pages?space-id=12345678&cursor=eyJpZCI6IjYyNTU0MzE0IiwiY29udGVudE9yZGVyIjoiaWQiLCJjb250ZW50T3JkZXJWYWx1ZSI6NjI1NTQzMTR9",
                "base": "https://my-tenant.atlassian.net/wiki"
            }
        }

    カーソルはレスポンスの "next" キーから抽出され、次のリクエストのクエリパラメータとして使用されます。
    """

    def __init__(
        self,
        cursor_path: jsonpath.TJsonPath = "_links.next",
        cursor_param: str = "cursor",
    ):
        """
        Args:
            cursor_path: Json内でのカーソルのキーまでのパス
            cursor_param: カーソルのトークンを示すクエリパラメータ

        Examples:
            以下のJsonならば
            {
              "_links": {
                   "next": "/wiki/api/v2/pages?space-id=12345678&cursor=eyJpZCI6IjYyNTU0MzE0IiwiY29udGVudE9yZGVyIjoiaWQiLCJjb250ZW50T3JkZXJWYWx1ZSI6NjI1NTQzMTR9",
                   "base": "https://my-tenant.atlassian.net/wiki"
               }
            }
            >>> ConfluenceV2CursorPagenator("_links.next", "cursor")
        """
        super().__init__()
        self.cursor_path = jsonpath.compile_path(cursor_path)
        self.cursor_param = cursor_param
    
    def update_state(self, response: Response, data = None) -> None:
        values = jsonpath.find_values("_links.next", response.json())
        next_path = values[0] if values else None
        self._next_reference = next_path.split("cursor=")[1].split("&")[0] if next_path else None

    def update_request(self, request: Request) -> None:
        if request.params is None:
            request.params = {}

        request.params["cursor"] = self._next_reference

v1_client = RESTClient(
    base_url=urljoin(dlt.secrets["credentials.CONFLUENCE_BASE_URL"], "wiki/rest/api"),
    auth=HttpBasicAuth(
        username=dlt.secrets["credentials.CONFLUENCE_USERNAME"],
        password=dlt.secrets["credentials.CONFLUENCE_API_TOKEN"]
    ),
)
v2_client = RESTClient(
    base_url=urljoin(dlt.secrets["credentials.CONFLUENCE_BASE_URL"],"wiki/api/v2"),
    auth=HttpBasicAuth(
        username=dlt.secrets["credentials.CONFLUENCE_USERNAME"],
        password=dlt.secrets["credentials.CONFLUENCE_API_TOKEN"]
    ),
    paginator=ConfluenceV2CursorPagenator()
)

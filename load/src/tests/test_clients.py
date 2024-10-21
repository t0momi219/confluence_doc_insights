import pytest
import json
from pathlib import Path

from unittest.mock import Mock

from requests.models import Response, Request

from load.clients import ConfluenceV2CursorPagenator

@pytest.mark.usefixtures("mock_api_server", "setup_mocks")
@pytest.mark.unit
class TestConfluenceV2CursorPagenator:

    def test__update_state__has_next_page(self):
        """test__update_state__has_next_page
        Paginatorのupdate_stateメソッド単体テスト
        """
        paginator = ConfluenceV2CursorPagenator()
        response = Mock(
            Response,
            json=lambda: {
                "_links": {
                    "next": "resource?cursor=test-cursor",
                    "base": "https://api.example.com/wiki/rest/api/resource",
                }
            },
        )
        paginator.update_state(response)
        assert paginator._next_reference == "test-cursor"
        assert paginator.has_next_page is True

    def test__update_state__no_next_page(self):
        """test__update_state__no_next_page
        Paginatorのupdate_stateメソッド単体テスト
        """
        paginator = ConfluenceV2CursorPagenator()
        response = Mock(Response, json=lambda: {"_links": {"base": ""}})
        paginator.update_state(response)
        assert paginator._next_reference is None
        assert paginator.has_next_page is False

    def test__update_request__has_next_page(self):
        """test__update_request__has_next_page
        Paginatorのupdate_requestメソッド単体テスト
        """
        paginator = ConfluenceV2CursorPagenator()
        paginator._next_reference = "test-cursor"
        request = Request(method="GET", url="https://api.example.com/wiki/rest/api/resource")
        paginator.update_request(request)
        assert request.params["cursor"] == "test-cursor"

    def test__update_request__no_next_page(self):
        """test__update_request__no_next_page
        Paginatorのupdate_requestメソッド単体テスト
        """
        paginator = ConfluenceV2CursorPagenator()
        paginator._next_reference = None
        request = Request(method="GET", url="https://api.example.com/wiki/rest/api/resource")
        paginator.update_request(request)
        assert request.params["cursor"] is None

    def test__paginator(self, v2_rest_client):
        """test__paginator
        
        Paginatorを用いたリクエストのテスト
        このPaginatorを与えられたRESTClientが、リクエストのレスポンスに含まれるカーソル情報をもとに、
        次のリクエストを送信することを確認する。
        """
        paginator = ConfluenceV2CursorPagenator()
        pages_iterator = v2_rest_client.paginate(
            "/cursor-response", paginator=paginator
        )
        pages = list(pages_iterator)

        assert len(pages) == 2
        BASE_DIR = Path(__file__).resolve().parent.parent
        assert pages[0][0] == json.load(
            open(Path(BASE_DIR / "tests/testdata/cursor_response_page1.json"))
        )
        assert pages[1][0] == json.load(
            open(Path(BASE_DIR / "tests/testdata/cursor_response_page2.json"))
        )

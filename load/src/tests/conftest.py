import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import requests_mock

from dlt.sources.helpers.rest_client import RESTClient

import dlt

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_URL = "https://api.example.com/"
V1_API_RELATIVE_PATH = "wiki/rest/api"
V2_API_RELATIVE_PATH = "wiki/api/v2"

def flatten_dict(nested_dict, prefix=""):
    """
    ネストされた辞書をフラット化します。

    Args:
        nested_dict (dict): フラット化するネストされた辞書。
        prefix (str): 現在のキーのレベルに使用する接頭辞（再帰に使用）。

    Returns:
        dict: 入力辞書のフラット化されたバージョン。

    Examples:
        >>> flatten_dict({'a': 1, 'b': {'c': 2, 'd': 3}})
            {'a': 1, 'b.c': 2, 'a.d': 3}
        >>> flatten_dict({'x': {'y': {'z': 1}}, 'p': {'q': 2}})
            {'x.y.z': 1, 'p.q': 2}
    """
    flattened = {}
    for key, value in nested_dict.items():
        new_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            # If the value is a dictionary, recurse
            flattened.update(flatten_dict(value, new_key))
        else:
            # If the value is not a dictionary, add it to the flattened dict
            flattened[new_key] = value

    return flattened


@pytest.fixture
def setup_mocks(monkeypatch):
    """setup_mocks
    dlt.configとdlt.secrets、日付関数をモック化します。
    """
    config = json.load(open(Path(BASE_DIR / "tests/testdata/dlt_config.json")))
    secrets = json.load(open(Path(BASE_DIR / "tests/testdata/dlt_secrets.json")))

    monkeypatch.setattr(dlt, "config", flatten_dict(config))
    monkeypatch.setattr(dlt, "secrets", flatten_dict(secrets))

    datetime_mock = MagicMock(wraps=datetime.datetime)
    datetime_mock.now.return_value = datetime.datetime(2024, 2, 1, 0, 0, 0)
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

@pytest.fixture(scope="module")
def mock_api_server():
    """mock_api_server
    
    テスト用のAPIサーバをモック化します。
    
    Examples:
        >>> @pytest.mark.usefixtures("mock_api_server")
        ... class TestClass:
        ...     def test__request(self):
        ...         res = client.paginate("/test-endpoint")
        ...         assert res == xxx # このクラスでモック化されたAPIレスポンスになります。
    """
    endpoints = [
        {
            # Paginatorテスト用
            "base_url": BASE_URL + V2_API_RELATIVE_PATH,
            "path": "/cursor-response",
            "response": json.load(
                open(Path(BASE_DIR / "tests/testdata/cursor_response_page1.json"))
            ),
        },
        {
            # Paginatorテスト用
            "base_url": BASE_URL + V2_API_RELATIVE_PATH,
            "path": "/cursor-response?cursor=test-cursor-1",
            "response": json.load(
                open(Path(BASE_DIR / "tests/testdata/cursor_response_page2.json"))
            ),
        },
        {
            # Confluence.get_spacesテスト用
            "base_url": BASE_URL + V2_API_RELATIVE_PATH,
            "path": "/spaces",
            "response": json.load(
                open(Path(BASE_DIR / "tests/testdata/spaces_response_multi_space_page1.json"))
            ),
        },
        {
            # Confluence.get_spacesテスト用
            "base_url": BASE_URL + V2_API_RELATIVE_PATH,
            "path": "/spaces?cursor=test-cursor-1",
            "response": json.load(
                open(Path(BASE_DIR / "tests/testdata/spaces_response_multi_space_page2.json"))
            ),
        },
        {
            # Confluence.get_spacesテスト用
            "base_url": BASE_URL + V2_API_RELATIVE_PATH,
            "path": "/spaces?keys=test-space-1",
            "response": json.load(
                open(Path(BASE_DIR / "tests/testdata/spaces_response_selected_space.json"))
            ),
        },
        {
            # Confluence.get_pagesテスト用
            "base_url": BASE_URL + V2_API_RELATIVE_PATH,
            "path": "/spaces/1111111/pages?body-format=storage",
            "response": json.load(
                open(Path(BASE_DIR / "tests/testdata/pages_response_page1.json"))
            ),
        },
        {
            # Confluence.get_pagesテスト用
            "base_url": BASE_URL + V2_API_RELATIVE_PATH,
            "path": "/spaces/1111111/pages?body-format=storage&cursor=test-cursor-1",
            "response": json.load(
                open(Path(BASE_DIR / "tests/testdata/pages_response_page2.json"))
            ),
        },
    ]
    with requests_mock.Mocker() as m:
        # モック化するエンドポイントを登録
        for endpoint in endpoints:
            m.get(endpoint["base_url"] + endpoint["path"], json=endpoint["response"])

        yield m


@pytest.fixture
def v1_rest_client():
    v1_client = RESTClient(
        base_url=BASE_URL + V1_API_RELATIVE_PATH,
        headers={"Accept": "application/json"},
    )
    with patch("load.clients.v1_client", v1_client):
        yield v1_client


@pytest.fixture
def v2_rest_client():
    v2_client = RESTClient(
        base_url=BASE_URL + V2_API_RELATIVE_PATH,
        headers={"Accept": "application/json"},
    )
    with patch("load.clients.v2_client", v2_client):
        yield v2_client

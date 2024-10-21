import json
from pathlib import Path
import pytest

@pytest.mark.usefixtures("mock_api_server", "setup_mocks")
@pytest.mark.unit
class TestConfluenceSource:

    def test__get_spaces__all_spaces(self, v2_rest_client):
        """test__get_spaces__all_spaces
        Confluence.get_spacesのテスト
        target_spaces を指定しない場合、全スペースを取得する
        """
        # :NOTE confluence sourceのインポートはここでなければ、引数のv2_rest_clientが
        # モックされないため、ここでimportしている
        # ここから動かさないで！&引数からv2_rest_clientを削除しないで！
        from load.confluence import confluence

        target_spaces = []
        sources = confluence(target_spaces, 0)
        get_spaces = sources.resources["spaces"]

        spaces = list(get_spaces())
        assert len(spaces) == 6

    def test__get_spaces__selected_spaces(self, v2_rest_client):
        """test__get_spaces__selected_spaces
        Confluence.get_spacesのテスト
        target_spaces を指定した場合、指定したスペースのみを取得する
        """
        # :NOTE confluence sourceのインポートはここでなければ、引数のv2_rest_clientが
        # モックされないため、ここでimportしている.
        # ここから動かさないで！&引数からv2_rest_clientを削除しないで！
        from load.confluence import confluence

        target_spaces = ["test-space-1"]
        sources = confluence(target_spaces, 0)
        get_spaces = sources.resources["spaces"]

        spaces = list(get_spaces())
        assert len(spaces) == 1

    def test__get_pages(self, v2_rest_client):
        """test__get_pages
        Confluence.get_pagesのテスト
        """
        # :NOTE confluence sourceのインポートはここでなければ、引数のv2_rest_clientが
        # モックされないため、ここでimportしている
        # ここから動かさないで！&引数からv2_rest_clientを削除しないで！
        from load.confluence import confluence

        target_spaces = ["test-space-1"]
        sources = confluence(target_spaces, 0)
        get_pages = sources.resources["pages"]

        pages = list(get_pages())
        assert len(pages) == 4

        BASE_DIR = Path(__file__).resolve().parent.parent
        actual_data_page1 = json.load(
            open(Path(BASE_DIR / "tests/testdata/pages_response_page1.json"))
        )
        actual_data_page2 = json.load(
            open(Path(BASE_DIR / "tests/testdata/pages_response_page2.json"))
        )
        actual_data = actual_data_page1["results"] + actual_data_page2["results"]

        assert pages == actual_data

    @pytest.mark.parametrize(
            [
                "days_num",
                "tz_name",
                "expected"
            ],
            [
                pytest.param(
                    0,
                    "Asia/Tokyo",
                    [{"date": "2024-02-01"}]
                ),
                pytest.param(
                    1,
                    "Asia/Tokyo",
                    [{"date": "2024-02-01"}, {"date": "2024-01-31"}]
                )
            ]
    )
    def test__get_date_range(self, days_num, tz_name, expected):
        """test__get_date_range
        Confluence.get_date_rangeのテスト
        """
        # :NOTE インポートをここから動かさないで！
        from load.confluence import get_date_range

        actual = get_date_range(days_num, tz_name)
        assert actual == expected


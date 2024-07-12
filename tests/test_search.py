import pytest

from ado_wrapper.resources.searches import CodeSearch, CodeSearchHit
from tests.setup_client import setup_client, test_search_string  # fmt: skip


class TestCodeSearch:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        search = CodeSearch.from_request_payload(
            {
                "repository": {"name": "test-repo", "id": "123456789"},
                "path": "test/path/here.txt",
                "fileName": "here.txt",
                "project": {"name": "my-test-project"},
                "versions": [{"branchName": "test-branch"}],
                "matches": {
                    "content": [
                        {
                            "charOffset": 0,
                            "length": 1,
                            "line": 1,
                            "column": 1,
                            "codeSnippet": None,
                            "type": "content",
                        },
                    ],
                },
            }
        )
        assert search.repository_name == "test-repo"
        assert search.repository_id == "123456789"
        assert search.path == "test/path/here.txt"
        assert search.file_name == "here.txt"
        assert search.project == "my-test-project"
        assert search.branch_name == "test-branch"
        assert search.matches == [CodeSearchHit(0, 1, 1, 1, None, "content")]

    @pytest.mark.from_request_payload
    def test_create_delete(self) -> None:
        search_results = CodeSearch.get_by_search_string(self.ado_client, test_search_string)
        assert len(search_results) > 10
        search_results = CodeSearch.get_by_search_string(self.ado_client, test_search_string, 1)
        assert len(search_results) == 1
        search_results = CodeSearch.get_by_search_string(self.ado_client, test_search_string, 5, sort_direction="DESC")
        assert len(search_results) == 5

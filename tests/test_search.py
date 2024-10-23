import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.errors import ConfigurationError
from ado_wrapper.resources.searches import CodeSearch, CodeSearchHit
from ado_wrapper.resources.commits import Commit
from ado_wrapper.resources.repo import Repo
from ado_wrapper.utils import TemporaryResource

from tests.setup_client import setup_client, REPO_PREFIX


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

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        TEXT = "abcdef123456"
        with TemporaryResource(self.ado_client, Repo, name=REPO_PREFIX + "code-search") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"text.txt": TEXT}, "add", "Add initial")
            Commit.create(self.ado_client, repo.repo_id, "my-branch", "my-branch", {"text2.txt": TEXT}, "add", "Add initial 2")
            with pytest.raises(ConfigurationError):
                search_results = CodeSearch.get_by_search_string(self.ado_client, TEXT)
                assert len(search_results) == 2
            with pytest.raises(ConfigurationError):
                search_results = CodeSearch.get_by_search_string(self.ado_client, TEXT, 1)
                assert len(search_results) == 1
            with pytest.raises(ConfigurationError):
                search_results = CodeSearch.get_by_search_string(self.ado_client, TEXT, 2, sort_direction="DESC")
                assert len(search_results) == 2


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

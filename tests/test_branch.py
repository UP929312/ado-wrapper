import pytest

from ado_wrapper.resources.branches import Branch
from ado_wrapper.resources.commits import Commit

from tests.setup_client import setup_client, RepoContextManager


class TestBranch:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        branch = Branch.from_request_payload(
            {
                "name": "main",
                "isMain": True,
                "isDeleted": False,
                "isProtected": True,
                "objectId": "123",
                "url": "https://dev.azure.com/...",
                "repository": {"id": "123", "name": "test-repo"},
            }
        )
        assert branch.to_json() == Branch.from_json(branch.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_branch(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-branch") as repo:
            with pytest.raises(NotImplementedError):
                Branch.create(self.ado_client, "", "", "")
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"text.txt": "Contents of the file"}, "add", "Test commmit 1")
            branch = Branch.get_all_by_repo(self.ado_client, repo.repo_id)
            assert branch[0].name == "test-branch" or branch[1].name == "test-branch"

# ======================================================================================================================

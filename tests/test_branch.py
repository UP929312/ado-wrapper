import pytest

from client import AdoClient
from resources.branches import Branch
from resources.repo import Repo
from resources.commits import Commit


with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()


class TestBranch:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

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
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-branches")
        with pytest.raises(NotImplementedError):
            Branch.create(self.ado_client, "", "", "")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"text.txt": "Contents of the file"}, "add", "Test commmit 1")
        branch = Branch.get_all_by_repo(self.ado_client, repo.repo_id)
        assert branch[0].name == "test-branch" or branch[1].name == "test-branch"
        repo.delete(self.ado_client)


# ======================================================================================================================

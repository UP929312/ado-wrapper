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
                Branch.create(self.ado_client, "", "")
            Commit.create(
                self.ado_client, repo.repo_id, "main", "test-branch", {"text.txt": "Contents of the file"}, "add", "Test commmit 1"
            )
            branches = Branch.get_all_by_repo(self.ado_client, repo.repo_id)
            non_main_branch = [branch for branch in branches if branch.name != "main"][0]
            assert non_main_branch.name == "test-branch"
            with pytest.raises(NotImplementedError):
                Branch.delete_by_id(self.ado_client, repo.repo_id, non_main_branch.branch_id)

    def test_get_certain_branches(self) -> None:
        with RepoContextManager(self.ado_client, "get-certain-branches") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch-1", {"text.txt": "Contents"}, "add", "Commmit 1")
            branch = Branch.get_by_name(self.ado_client, repo.repo_id, "test-branch-1")
            assert branch is not None
            assert branch.name == "test-branch-1"

            id_branch = Branch.get_by_id(self.ado_client, repo.repo_id, branch.branch_id)
            assert id_branch is not None
            assert id_branch.name == "test-branch-1"

            # main_branch = Branch.get_main_branch(self.ado_client, repo.repo_id)
            # assert main_branch.is_main
            # assert main_branch.name == "main"
            # protected_branches = Branch.get_protected_branches(self.ado_client, repo.repo_id)
            # assert len(protected_branches) == 1
            # assert protected_branches[0].is_protected
            # deleted_branches = Branch.get_deleted_branches(self.ado_client, repo.repo_id)
            # assert len(deleted_branches) == 0
            # active_branches = Branch.get_active_branches(self.ado_client, repo.repo_id)
            # assert len(active_branches) == 2

            with pytest.raises(NotImplementedError):
                branch.delete(self.ado_client)

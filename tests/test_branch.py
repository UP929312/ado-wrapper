import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.branches import Branch
from ado_wrapper.resources.commits import Commit
from tests.setup_client import RepoContextManager, setup_client


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
                "creator": {"displayName": "test", "uniqueName": "test", "id": "123"},
            }
        )
        assert branch.to_json() == Branch.from_json(branch.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_branch(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-branch") as repo:
            branch = Branch.create(self.ado_client, repo.repo_id, "test-branch")
            Branch.delete_by_id(self.ado_client, branch.name, repo.repo_id)

    @pytest.mark.create_delete
    def test_create_delete_multiple_branches(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-multiple-branches") as repo:
            branch1 = Branch.create(self.ado_client, repo.repo_id, "test-branch")
            branch2 = Branch.create(self.ado_client, repo.repo_id, "test-branch2")
            Branch.delete_by_id(self.ado_client, branch1.name, repo.repo_id)
            Branch.delete_by_id(self.ado_client, branch2.name, repo.repo_id)

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

            branch.delete(self.ado_client)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vvvv"])
    # pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

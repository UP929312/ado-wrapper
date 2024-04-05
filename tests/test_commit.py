import pytest

from ado_wrapper.client import AdoClient
from ado_wrapper.resources.repo import Repo
from ado_wrapper.resources.commits import Commit

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()  # fmt: skip


class TestCommit:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project, state_file_name="tests/test_state.state")

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        commit = Commit.from_request_payload(
            {
                "commitId": "123",
                "author": {"name": "test-author", "email": "test-email", "date": "2021-08-01T00:00:00Z"},
                "comment": "Test commit",
            }
        )
        assert commit.commit_id == "123"
        assert commit.author.name == "test-author"
        assert commit.message == "Test commit"
        assert commit.to_json() == Commit.from_json(commit.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-create-delete-commit")
        commit = Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        assert commit.message == "Test commit"
        repo.delete(self.ado_client)

    def test_get_latest_by_repo(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-get-latest-commit")
        commit = Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        lastest_commit = Commit.get_latest_by_repo(self.ado_client, repo.repo_id, "test-branch")
        assert lastest_commit is not None
        assert commit.commit_id == lastest_commit.commit_id
        assert commit.author.member_id == lastest_commit.author.member_id
        assert commit.message == lastest_commit.message
        repo.delete(self.ado_client)

    def test_get_all(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-get-all-commits")
        Commit.create(self.ado_client, repo.repo_id, "main", "new-branch", {"test.txt": "This is one thing"}, "add", "Test commit 1")
        Commit.create(
            self.ado_client, repo.repo_id, "new-branch", "new-branch2", {"test2.txt": "This is something else"}, "add", "Test commit 2"
        )
        all_commits = Commit.get_all_by_repo(self.ado_client, repo.repo_id)
        assert len(all_commits) == 2 + 1  # 1 For the initial README commit
        assert all(isinstance(commit, Commit) for commit in all_commits)
        repo.delete(self.ado_client)

    def test_get_all_with_branch(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-get-all-commits-with-branch")
        Commit.create(self.ado_client, repo.repo_id, "main", "new-branch", {"test.txt": "This is one thing"}, "add", "Test commit 1")  # fmt: skip
        Commit.create(self.ado_client, repo.repo_id, "new-branch", "new-branch", {"test2.txt": "This is something else"}, "add", "Test commit 2")  # fmt: skip
        Commit.create(self.ado_client, repo.repo_id, "main", "other-branch", {"test3.txt": "Even more something else"}, "add", "Test commit 3")  # fmt: skip
        all_commits = Commit.get_all_by_repo(self.ado_client, repo.repo_id, "new-branch")
        assert len(all_commits) == 2 + 1  # 1 For the initial README commit
        assert all(isinstance(commit, Commit) for commit in all_commits)
        repo.delete(self.ado_client)

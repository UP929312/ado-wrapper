import pytest

from client import AdoClient
from resources.repo import Repo
from resources.pull_requests import PullRequest
from resources.commits import Commit

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()


class TestRepo:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        repo = Repo.from_request_payload({"id": "123", "name": "test-repo", "defaultBranch": "master"})
        assert isinstance(repo, Repo)
        assert repo.repo_id == "123"
        assert repo.name == "test-repo"
        assert repo.default_branch == "master"
        assert not repo.is_disabled
        assert repo.to_json() == Repo.from_json(repo.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-create-delete-repo")
        assert repo.name == "ado-api-test-repo-for-create-delete-repo"
        repo.delete(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-update-repo")
        Commit.create(
            self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit"
        )  # Create a branch
        # =====
        repo.update(self.ado_client, "name", "ado-api-test-repo-for-update-repo-renamed")
        assert repo.name == "ado-api-test-repo-for-update-repo-renamed"  # Test instance attribute is updated
        repo.update(self.ado_client, "default_branch", "refs/heads/test-branch")
        assert repo.default_branch == "refs/heads/test-branch"  # Test instance attribute is updated
        # =====
        fetched_repo = Repo.get_by_id(self.ado_client, repo.repo_id)
        assert fetched_repo.name == "ado-api-test-repo-for-update-repo-renamed"
        assert fetched_repo.default_branch == "test-branch"
        # =====
        repo.update(self.ado_client, "is_disabled", True)
        assert repo.is_disabled
        repo.update(self.ado_client, "is_disabled", False)  # Disabled repos can't be deleted
        # =====
        repo.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        repo_created = Repo.create(self.ado_client, "ado-api-test-repo-for-get-repo-by-id")
        repo = Repo.get_by_id(self.ado_client, repo_created.repo_id)
        assert repo.repo_id == repo_created.repo_id
        repo_created.delete(self.ado_client)

    def test_get_all(self) -> None:
        repos = Repo.get_all(self.ado_client)
        assert len(repos) > 10
        assert all(isinstance(repo, Repo) for repo in repos)

    def test_get_by_name(self) -> None:
        repo_created = Repo.create(self.ado_client, "ado-api-test-repo-for-get-repo-by-name")
        repo = Repo.get_by_name(self.ado_client, "ado-api-test-repo-for-get-repo-by-name")
        assert repo.name == repo_created.name
        assert repo.repo_id == repo_created.repo_id
        repo_created.delete(self.ado_client)

    def test_get_file(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-get-file")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"read-this.txt": "Delete me!"}, "add", "Test commit")
        file = repo.get_file(self.ado_client, "README.md", "test-branch")
        assert len(file) > 5
        repo.delete(self.ado_client)

    def test_get_repo_contents(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-get-repo-contents")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        contents = repo.get_repo_contents(self.ado_client)
        assert len(contents.keys()) == 1
        assert isinstance(contents, dict)
        repo.delete(self.ado_client)

    def test_get_pull_requests(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-get-pull-requests")
        Commit.create(
            self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "This should be on the branch"}, "add", "Test commit"
        )
        repo.create_pull_request(self.ado_client, "test-branch", "Test PR", "Test PR description")
        pull_requests = repo.get_all_pull_requests(self.ado_client, repo_id=repo.repo_id, status="all")
        assert len(pull_requests) == 1
        assert all(isinstance(pr, PullRequest) for pr in pull_requests)
        pull_requests[0].close(self.ado_client)
        repo.delete(self.ado_client)

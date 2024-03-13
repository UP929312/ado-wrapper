from client import AdoClient
from repository import Repo
from pull_requests import PullRequest

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, existing_repo_name, existing_repo_id, *_ = test_data.read().splitlines()  # fmt: skip


class TestRepo:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

    def test_from_request_payload(self) -> None:
        repo = Repo.from_request_payload({"id": "123", "name": "test-repo", "defaultBranch": "refs/heads/master"})
        assert isinstance(repo, Repo)
        assert repo.repo_id == "123"
        assert repo.name == "test-repo"
        assert repo.default_branch == "refs/heads/master"
        assert repo.is_disabled == False

    def test_get_by_id(self) -> None:
        repo = Repo.get_by_id(self.ado_client, existing_repo_id)
        assert repo.repo_id == existing_repo_id

    def test_create_delete(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo")
        assert repo.name == "ado-api-test-repo"
        repo.delete(self.ado_client)

    def test_get_all(self) -> None:
        repos = Repo.get_all(self.ado_client)
        assert len(repos) > 10
        assert all([isinstance(repo, Repo) for repo in repos])

    def test_get_by_name(self) -> None:
        repo = Repo.get_by_name(self.ado_client, existing_repo_name)
        assert repo.name == existing_repo_name

    def test_get_file(self) -> None:
        repo = Repo.get_by_name(self.ado_client, existing_repo_name)
        file = repo.get_file(self.ado_client, "README.md")
        assert len(file) > 10

    def test_get_repo_contents(self) -> None:
        repo = Repo.get_by_name(self.ado_client, existing_repo_name)
        contents = repo.get_repo_contents(self.ado_client)
        assert len(contents.keys()) > 10
        assert isinstance(contents, dict)

    def test_create_pull_request(self) -> None:
        pass
        # repo = Repo.get_by_name(self.ado_client, existing_repo_name)
        # pr = repo.create_pull_request(self.ado_client, "ado-api-test-branch", "Test PR", "Test PR description")
        # assert pr.title == "Test PR"
        # pr.close(self.ado_client)

    def test_get_pull_requests(self) -> None:
        repo = Repo.get_by_name(self.ado_client, existing_repo_name)
        pull_requests = repo.get_all_pull_requests(self.ado_client, "all")
        assert len(pull_requests) > 1
        assert all([isinstance(pr, PullRequest) for pr in pull_requests])

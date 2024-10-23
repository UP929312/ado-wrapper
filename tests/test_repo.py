import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.commits import Commit
from ado_wrapper.resources.pull_requests import PullRequest
from ado_wrapper.resources.repo import Repo
from ado_wrapper.utils import TemporaryResource

from tests.setup_client import setup_client, REPO_PREFIX


class TestRepo:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

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
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-create-delete-repo")
        assert repo.name == "ado_wrapper-test-repo-for-create-delete-repo"
        repo.delete(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-update-repo")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        # =====
        repo.update(self.ado_client, "name", "ado_wrapper-test-repo-for-update-repo-renamed")
        assert repo.name == "ado_wrapper-test-repo-for-update-repo-renamed"  # Test instance attribute is updated
        repo.update(self.ado_client, "default_branch", "refs/heads/test-branch")
        assert repo.default_branch == "refs/heads/test-branch"  # Test instance attribute is updated
        # =====
        fetched_repo = Repo.get_by_id(self.ado_client, repo.repo_id)
        assert fetched_repo.name == "ado_wrapper-test-repo-for-update-repo-renamed"
        assert fetched_repo.default_branch == "test-branch"
        # =====
        repo.update(self.ado_client, "is_disabled", True)
        assert repo.is_disabled
        repo.update(self.ado_client, "is_disabled", False)  # Disabled repos can't be deleted
        # =====
        repo.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        repo_created = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-get-repo-by-id")
        repo = Repo.get_by_id(self.ado_client, repo_created.repo_id)
        assert repo.repo_id == repo_created.repo_id
        repo_created.delete(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        repos = Repo.get_all(self.ado_client)
        assert len(repos) >= 1
        assert all(isinstance(repo, Repo) for repo in repos)

    @pytest.mark.get_all_by_name
    def test_get_by_name(self) -> None:
        repo_created = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-get-repo-by-name")
        repo = Repo.get_by_name(self.ado_client, "ado_wrapper-test-repo-for-get-repo-by-name")
        assert repo is not None
        assert repo.name == repo_created.name
        assert repo.repo_id == repo_created.repo_id
        repo_created.delete(self.ado_client)

    def test_get_file(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-get-file")
        assert repo is not None
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"read-this.txt": "Delete me!"}, "add", "Test commit")
        file = repo.get_file(self.ado_client, "README.md", "test-branch")
        assert len(file) > 5
        repo.delete(self.ado_client)

    def test_get_contents(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-get-repo-contents")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        contents = repo.get_contents(self.ado_client)
        assert len(contents.keys()) == 1
        assert isinstance(contents, dict)
        repo.delete(self.ado_client)

    def test_get_pull_requests(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-get-pull-requests")
        Commit.create(
            self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "This should be on the branch"}, "add", "Test commit"
        )
        repo.create_pull_request(self.ado_client, "test-branch", "Test PR", "Test PR description")
        pull_requests = repo.get_all_pull_requests(self.ado_client, repo_id=repo.repo_id, status="all")
        assert len(pull_requests) == 1
        assert all(isinstance(pr, PullRequest) for pr in pull_requests)
        pull_requests[0].close(self.ado_client)
        repo.delete(self.ado_client)

    @pytest.mark.create_delete
    def test_gitignore_templates(self) -> None:
        # Readme only
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-gitignore-templates-1", include_readme=True)
        repo_contents = repo.get_contents(self.ado_client)
        assert list(repo_contents.keys()) == ["README.md"]
        repo.delete(self.ado_client)

        # Git ignore template only
        repo = Repo.create(
            self.ado_client, "ado_wrapper-test-repo-for-gitignore-templates-2", include_readme=False, git_ignore_template="Python"
        )
        repo_contents = repo.get_contents(self.ado_client)
        assert ".gitignore" in repo_contents
        assert "README.md" not in repo_contents
        repo.delete(self.ado_client)

        # Both
        repo = Repo.create(
            self.ado_client, "ado_wrapper-test-repo-for-gitignore-templates-3", include_readme=True, git_ignore_template="Python"
        )
        repo_contents = repo.get_contents(self.ado_client)
        assert ".gitignore" in repo_contents
        assert "README.md" in repo_contents
        repo.delete(self.ado_client)

    # @pytest.mark.wip
    def test_repo_get_and_decode_file(self) -> None:
        with TemporaryResource(self.ado_client, Repo, name=REPO_PREFIX + "get-and-decode-file") as repo:
            # JSON
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"test.json": '{"a": 123, "b": 456}'})
            file_contents = repo.get_and_decode_file(self.ado_client, "test.json", "my-branch")
            assert isinstance(file_contents, dict)
            # YAML
            Commit.create(self.ado_client, repo.repo_id, "my-branch", "my-branch", {"test.yaml": "a: 123\nb: 456\n"})
            file_contents = repo.get_and_decode_file(self.ado_client, "test.yaml", "my-branch")
            assert isinstance(file_contents, dict)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

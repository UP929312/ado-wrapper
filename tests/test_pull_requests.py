import pytest

from client import AdoClient
from resources.repo import Repo
from resources.commits import Commit
from resources.pull_requests import PullRequest

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()  # fmt: skip


class TestPullRequest:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        pull_request = PullRequest.from_request_payload(
            {
                "createdBy": {"displayName": "test-author", "uniqueName": "test-author", "id": "123"},
                "reviewers": [],
                "repository": {"id": "123", "name": "test-repo"},
                "pullRequestId": 123,
                "title": "Test PR",
                "description": "Test PR description",
                "sourceRefName": "main",
                "targetRefName": "main",
                "creationDate": "2021-08-01T00:00:00Z",
                "closedDate": "2021-08-01T00:00:00Z",
                "isDraft": False,
                "mergeStatus": "notSet",
            }
        )
        assert pull_request.pull_request_id == "123"
        assert pull_request.author.name == "test-author"
        assert pull_request.description == "Test PR description"
        assert pull_request.to_json() == PullRequest.from_json(pull_request.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-create-delete-pull-request")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        pull_request = PullRequest.create(self.ado_client, repo.repo_id, "test-branch", "Test PR for create-delete",
                                          "Test PR description", is_draft=True)  # fmt: skip
        assert pull_request.title == "Test PR for create-delete"
        assert pull_request.description == "Test PR description"
        assert pull_request.is_draft
        # assert [x.member_id for x in pull_request.reviewers] == [existing_user_id]
        pull_request.close(self.ado_client)
        repo.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-get-pull-request-by-id")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        pull_request_created = PullRequest.create(self.ado_client, repo.repo_id, "test-branch", "Test PR For Get PR By ID", "Test description")
        pull_request = PullRequest.get_by_id(self.ado_client, pull_request_created.pull_request_id)
        assert pull_request.pull_request_id == pull_request_created.pull_request_id
        pull_request_created.close(self.ado_client)
        repo.delete(self.ado_client)

    def test_get_all(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-get-pull-requests")
        Commit.create(self.ado_client, repo.repo_id, "main", "new-branch", {"test.txt": "This is one thing"}, "add", "Test commit 1")
        Commit.create(self.ado_client, repo.repo_id, "main", "new-branch2", {"test2.txt": "This is one thing"}, "add", "Test commit 2")
        pull_request_1 = PullRequest.create(self.ado_client, repo.repo_id, "new-branch", "Test PR For Get Pull Requests 1", "Test description")
        pull_request_2 = PullRequest.create(self.ado_client, repo.repo_id, "new-branch2", "Test PR For Get Pull Requests 1", "Test description")
        all_pull_requests = Repo.get_all_pull_requests(self.ado_client, repo_id=repo.repo_id, status="active")
        assert len(all_pull_requests) == 2
        assert all(isinstance(pull_request, PullRequest) for pull_request in all_pull_requests)
        assert all([x.pull_request_id in [pull_request_1.pull_request_id, pull_request_2.pull_request_id] for x in all_pull_requests])
        repo.delete(self.ado_client)

    def test_mark_as_draft(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-mark-as-draft")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        pull_request = PullRequest.create(self.ado_client, repo.repo_id, "test-branch", "Test PR for mark as drafk", "Test PR description")
        pull_request.mark_as_draft(self.ado_client)
        assert pull_request.is_draft
        pull_request.close(self.ado_client)
        repo.delete(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-update-pull-request")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
        pull_request = PullRequest.create(self.ado_client, repo.repo_id, "test-branch", "Test PR for Update", "Test PR description")
        # =====
        pull_request.update(self.ado_client, "title", "ado-api-test-repo-for-update-pull-request-renamed")
        assert pull_request.title == "ado-api-test-repo-for-update-pull-request-renamed"  # Test instance attribute is updated
        pull_request.update(self.ado_client, "description", "Updated description")
        assert pull_request.description == "Updated description"  # Test instance attribute is updated
        pull_request.update(self.ado_client, "status", "succeeded")
        assert pull_request.status == "succeeded"
        # =====
        fetched_pull_request = PullRequest.get_by_id(self.ado_client, pull_request.pull_request_id)
        assert fetched_pull_request.title == "ado-api-test-repo-for-update-pull-request-renamed"
        assert fetched_pull_request.description == "Updated description"
        assert fetched_pull_request.status == "succeeded"
        # =====
        pull_request.close(self.ado_client)
        repo.delete(self.ado_client)

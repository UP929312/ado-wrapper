import pytest

from ado_wrapper.resources.commits import Commit
from ado_wrapper.resources.pull_requests import PullRequest, PullRequestCommentThread
from ado_wrapper.resources.repo import Repo
from tests.setup_client import RepoContextManager, setup_client


class TestPullRequest:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

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
                "status": "notSet",
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
        with RepoContextManager(self.ado_client, "create-delete-pull-request") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
            pull_request = PullRequest.create(self.ado_client, repo.repo_id, "test-branch", "Test PR for create-delete",
                                            "Test PR description", is_draft=True)  # fmt: skip
            assert pull_request.title == "Test PR for create-delete"
            assert pull_request.description == "Test PR description"
            assert pull_request.is_draft
            pull_request.close(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        with RepoContextManager(self.ado_client, "repo-for-get-pull-request-by-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
            pull_request_created = PullRequest.create(
                self.ado_client, repo.repo_id, "test-branch", "Test PR For Get PR By ID", "Test description"
            )
            pull_request = PullRequest.get_by_id(self.ado_client, pull_request_created.pull_request_id)
            assert pull_request.pull_request_id == pull_request_created.pull_request_id
            pull_request_created.close(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        with RepoContextManager(self.ado_client, "repo-for-get-pull-requests") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "new-branch", {"test.txt": "This is one thing"}, "add", "Test commit 1")
            Commit.create(self.ado_client, repo.repo_id, "main", "new-branch2", {"test2.txt": "This is one thing"}, "add", "Test commit 2")
            pull_request_1 = PullRequest.create(
                self.ado_client, repo.repo_id, "new-branch", "Test PR For Get Pull Requests 1", "Test description"
            )
            pull_request_2 = PullRequest.create(
                self.ado_client, repo.repo_id, "new-branch2", "Test PR For Get Pull Requests 1", "Test description"
            )
            all_pull_requests = Repo.get_all_pull_requests(self.ado_client, repo_id=repo.repo_id, status="active")
            assert len(all_pull_requests) == 2
            assert all(isinstance(pull_request, PullRequest) for pull_request in all_pull_requests)
            assert all(x.pull_request_id in [pull_request_1.pull_request_id, pull_request_2.pull_request_id] for x in all_pull_requests)

    def test_mark_as_draft(self) -> None:
        with RepoContextManager(self.ado_client, "repo-for-mark-as-draft") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
            pull_request = PullRequest.create(
                self.ado_client, repo.repo_id, "test-branch", "Test PR for mark as drafk", "Test PR description"
            )
            # ----
            pull_request.mark_as_draft(self.ado_client)
            assert pull_request.is_draft
            # ----
            fetched_pull_request = PullRequest.get_by_id(self.ado_client, pull_request.pull_request_id)
            assert fetched_pull_request.is_draft
            # ----
            pull_request.close(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        with RepoContextManager(self.ado_client, "repo-for-update-pull-request") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"test.txt": "Delete me!"}, "add", "Test commit")
            pull_request = PullRequest.create(self.ado_client, repo.repo_id, "test-branch", "Test PR for Update", "Test PR description")
            # =====
            pull_request.update(self.ado_client, "title", "ado_wrapper-test-repo-for-update-pull-request-renamed")
            assert pull_request.title == "ado_wrapper-test-repo-for-update-pull-request-renamed"  # Test instance attribute is updated
            pull_request.update(self.ado_client, "description", "Updated description")
            assert pull_request.description == "Updated description"  # Test instance attribute is updated
            pull_request.update(self.ado_client, "is_draft", True)
            assert pull_request.is_draft == True
            # =====
            fetched_pull_request = PullRequest.get_by_id(self.ado_client, pull_request.pull_request_id)
            assert fetched_pull_request.title == "ado_wrapper-test-repo-for-update-pull-request-renamed"
            assert fetched_pull_request.description == "Updated description"
            assert fetched_pull_request.merge_status == "succeeded"
            # =====
            pull_request.close(self.ado_client)

    @pytest.mark.get_all
    def test_get_all_by_repo_id(self) -> None:
        with RepoContextManager(self.ado_client, "repo-for-get-all-by-repo-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "new-branch", {"test.txt": "This is one thing"}, "add", "Test commit 1")
            pull_request_1 = PullRequest.create(
                self.ado_client, repo.repo_id, "new-branch", "Test PR For Get Pull Requests 1", "Test description"
            )
            all_pull_requests = PullRequest.get_all_by_repo_id(self.ado_client, repo_id=repo.repo_id, status="active")
            assert len(all_pull_requests) == 1
            assert all(isinstance(pull_request, PullRequest) for pull_request in all_pull_requests)
            assert all(x.pull_request_id in [pull_request_1.pull_request_id] for x in all_pull_requests)

    def test_post_comment(self) -> None:
        with RepoContextManager(self.ado_client, "repo-for-post-comment") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "new-branch", {"test.txt": "Change"}, "add", "Test commit")
            pull_request = PullRequest.create(self.ado_client, repo.repo_id, "new-branch", "Test PR For Post Comment", "")
            pull_request.post_comment(self.ado_client, "This is a test comment")
            pull_request_comments = pull_request.get_comments(self.ado_client, ignore_system_messages=True)
            assert len(pull_request_comments) == 1
            assert pull_request_comments[0].content == "This is a test comment"
            pull_request.close(self.ado_client)

    def test_comment_thread(self) -> None:
        with RepoContextManager(self.ado_client, "repo-for-comment-thread") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "new-branch", {"test.txt": "Change"}, "add", "Test commit")
            pull_request = PullRequest.create(self.ado_client, repo.repo_id, "new-branch", "Test PR For Comment Thread", "")
            pull_request.post_comment(self.ado_client, "This is a test comment")
            pull_request.post_comment(self.ado_client, "This is a another test comment")
            all_comments = pull_request.get_comments(self.ado_client, ignore_system_messages=True)
            assert len(all_comments) == 2
            comment_thread = PullRequestCommentThread.get_all(self.ado_client, repo.repo_id, pull_request.pull_request_id)
            assert len(comment_thread[0].comments) == 1
            pull_request.close(self.ado_client)

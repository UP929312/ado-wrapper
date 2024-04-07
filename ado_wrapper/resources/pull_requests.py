from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TYPE_CHECKING
from dataclasses import dataclass, field

import requests

from ado_wrapper.utils import from_ado_date_string, ResourceNotFound
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member, Reviewer

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.resources.repo import Repo

PullRequestEditableAttribute = Literal["title", "description", "merge_status", "is_draft"]
PullRequestStatus = Literal["active", "completed", "abandoned", "all", "notSet"]
MergeStatus = Literal["succeeded", "conflicts", "rejectedByPolicy", "rejectedByUser", "queued", "notSet"]
CommentType = Literal["system", "regular", "codeChange", "unknown"]
PrCommentStatus = Literal["active", "pending", "fixed", "wontFix", "closed"]


@dataclass
class PullRequest(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests?view=azure-devops-rest-7.1"""

    pull_request_id: str = field(metadata={"is_id_field": True})
    title: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True})
    source_branch: str = field(repr=False)
    target_branch: str = field(repr=False)
    author: Member
    creation_date: datetime = field(repr=False)
    repo: Repo
    close_date: datetime | None = field(default=None, repr=False)
    is_draft: bool = field(default=False, repr=False, metadata={"editable": True, "internal_name": "isDraft"})
    merge_status: MergeStatus = field(default="notSet", metadata={"editable": True, "internal_name": "status"})
    reviewers: list[Reviewer] = field(default_factory=list, repr=False)  # Static(ish)

    def __str__(self) -> str:
        return f"PullRequest(id={self.pull_request_id}, title={self.title}, repo_name={self.repo.name}, author={self.author!s}, status={self.merge_status})"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "PullRequest":
        from ado_wrapper.resources.repo import Repo  # Circular import

        author = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        reviewers = [Reviewer.from_request_payload(reviewer) for reviewer in data["reviewers"]]
        repository = Repo(data["repository"]["id"], data["repository"]["name"])
        return cls(str(data["pullRequestId"]), data["title"], data.get("description", ""), data["sourceRefName"],
                   data["targetRefName"], author, from_ado_date_string(data["creationDate"]), repository,
                   from_ado_date_string(data.get("closedDate")), data["isDraft"], data.get("mergeStatus", "notSet"), reviewers)  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, pull_request_id: str) -> "PullRequest":
        return super().get_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/pullrequests/{pull_request_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(  # type: ignore[override]
        cls, ado_client: AdoClient, repo_id: str, from_branch_name: str, pull_request_title: str,
        pull_request_description: str, is_draft: bool = False
    ) -> "PullRequest":  # fmt: skip
        """Takes a list of reviewer ids, a branch to pull into main, and an option to start as draft"""
        # https://stackoverflow.com/questions/64655138/add-reviewers-to-azure-devops-pull-request-in-api-call   <- Why we can't allow reviewers from the get go
        # , "reviewers": [{"id": reviewer_id for reviewer_id in reviewer_ids}]
        payload = {"sourceRefName": f"refs/heads/{from_branch_name}", "targetRefName": "refs/heads/main", "title": pull_request_title,
                   "description": pull_request_description, "isDraft": is_draft}  # fmt: skip
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullrequests?api-version=7.1",
            json=payload, auth=ado_client.auth,  # fmt: skip
        ).json()
        if request.get("message", "").startswith("TF401398"):
            raise ValueError("The branch you are trying to create a pull request from does not exist.")
        obj = cls.from_request_payload(request)
        ado_client.state_manager.add_resource_to_state(cls.__name__, obj.pull_request_id, obj.to_json())  # type: ignore[arg-type]
        return obj

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, pull_request_id: str) -> None:  # type: ignore[override]
        # raise NotImplementedError("You can't delete pull requests, only close them.")
        pr = cls.get_by_id(ado_client, pull_request_id)
        pr.update(ado_client, "merge_status", "abandoned")
        ado_client.state_manager.remove_resource_from_state("PullRequest", pull_request_id)

    def update(self, ado_client: AdoClient, attribute_name: PullRequestEditableAttribute, attribute_value: Any) -> None:  # type: ignore[override]
        return super().update(
            ado_client, "patch",
            f"/{ado_client.ado_project}/_apis/git/repositories/{self.repo.repo_id}/pullRequests/{self.pull_request_id}?api-version=7.1",
            attribute_name, attribute_value, {}  # fmt: skip
        )

    @classmethod
    def get_all(cls, ado_client: AdoClient, status: PullRequestStatus = "all") -> list[PullRequest]:  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/pullrequests?searchCriteria.status={status}&api-version=7.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def add_reviewer(self, ado_client: AdoClient, reviewer_id: str) -> None:
        return self.add_reviewer_static(ado_client, self.repo.repo_id, self.pull_request_id, reviewer_id)

    @staticmethod
    def add_reviewer_static(ado_client: AdoClient, repo_id: str, pull_request_id: str, reviewer_id: str) -> None:
        """Copy of the add_reviewer method, but static, i.e. if you have the repo id and pr id, you don't need to fetch them again"""
        request = requests.put(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/reviewers/{reviewer_id}?api-version=7.1",
                                json={"vote": "0", "isRequired": "true"}, auth=ado_client.auth)  # fmt: skip
        assert request.status_code < 300

    def close(self, ado_client: AdoClient) -> None:
        self.update(ado_client, "merge_status", "abandoned")

    def delete(self, ado_client: AdoClient) -> None:
        self.delete_by_id(ado_client, self.pull_request_id)

    def mark_as_draft(self, ado_client: AdoClient) -> None:
        return self.update(ado_client, "is_draft", True)

    def unmark_as_draft(self, ado_client: AdoClient) -> None:
        return self.update(ado_client, "is_draft", True)

    def get_reviewers(self, ado_client: AdoClient) -> list[Member]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo.repo_id}/pullRequests/{self.pull_request_id}/reviewers?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return [Member(reviewer["displayName"], reviewer["uniqueName"], reviewer["id"]) for reviewer in request["value"]]

    @classmethod
    def get_all_by_repo_id(cls, ado_client: AdoClient, repo_id: str, status: PullRequestStatus = "all") -> list[PullRequest]:
        pull_requests = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullrequests?searchCriteria.status={status}&api-version=7.1",
            auth=ado_client.auth,
        ).json()
        try:
            return [PullRequest.from_request_payload(pr) for pr in pull_requests["value"]]
        except KeyError:
            if pull_requests.get("message", "").startswith("TF401019"):
                print(f"Repo `{pull_requests['message'].split('identifier')[1].split(' ')[0]}` was disabled, or you had no access.")
                return []
            raise ResourceNotFound(pull_requests)  # pylint: disable=raise-missing-from

    @classmethod
    def get_all_by_author(cls, ado_client: AdoClient, author_email: str, status: PullRequestStatus = "all") -> list[PullRequest]:
        return [pr for pr in cls.get_all(ado_client, status) if pr.author.email == author_email]

    @classmethod
    def get_my_pull_requests(cls, ado_client: AdoClient) -> list[PullRequest]:
        """This is super tempremental, I have to do a bunch of splits, it's not official so might not work, the statuses are also numerical."""
        import json

        request = requests.get(f"https://dev.azure.com/{ado_client.ado_org}/_pulls", auth=ado_client.auth)
        raw_data = (
            request.text.split("application/json")[1].split('pullRequests"')[1].split("queries")[0].removeprefix(":").removesuffix(',"')
        )
        return [cls.from_request_payload(pr) for pr in json.loads(raw_data).values()]

    def get_comment_threads(self, ado_client: AdoClient, ignore_system_messages: bool = True) -> list[PullRequestCommentThread]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo.repo_id}/pullRequests/{self.pull_request_id}/threads?api-version=7.1",
            auth=ado_client.auth,
        ).json()["value"]
        comments = [PullRequestCommentThread.from_request_payload(data) for data in request]
        if ignore_system_messages:
            comments = [comment for comment in comments if comment.comments[0].comment_type != "system"]
        return comments

    def get_comments(self, ado_client: AdoClient, ignore_system_messages: bool = True) -> list[PullRequestComment]:
        """Gets a list of comments on a pull request, optionally ignoring system messages."""
        return [comment for thread in self.get_comment_threads(ado_client, ignore_system_messages) for comment in thread.comments]

    def post_comment(self, ado_client: AdoClient, content: str) -> PullRequestComment:
        payload = {"comments": [{"commentType": 1, "content": content}], "status": "1"}
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo.repo_id}/pullRequests/{self.pull_request_id}/threads?api-version=7.1",
            json=payload, auth=ado_client.auth,
        ).json()
        return PullRequestComment.from_request_payload(request["comments"][0])


@dataclass
class PullRequestCommentThread(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-thread-comments/list?view=azure-devops-rest-7.1
    Represents a chain of comments on a pull request, with the status e.g. Resolved, Active, etc."""
    thread_id: str
    status: str | None
    comments: list["PullRequestComment"]

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "PullRequestCommentThread":
        comments = [PullRequestComment.from_request_payload(comment) for comment in data["comments"]]
        return cls(data["id"], data.get("status"), comments)

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, pull_request_id: str, thread_id: str) -> PullRequestCommentThread:  # type: ignore[override]
        return super().get_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/threads/{thread_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(cls, ado_client: AdoClient, repo_id: str, pull_request_id: str, content: str) -> StateManagedResource:  # type: ignore[override]
        return super().create(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/threads?api-version=7.1",
            {"comments": [{"commentType": 1, "content": content}]},
        )

    def update(self, ado_client: AdoClient, attribute_name: PrCommentStatus, attribute_value: Any) -> None:  # type: ignore[override]
        raise NotImplementedError

    def delete_by_id(self, ado_client: AdoClient, repo_id: str, pull_request_id: str, thread_id: str) -> None:  # type: ignore[override]
        return super().delete_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/threads/{thread_id}?api-version=7.1",
            thread_id
        )

    @classmethod
    def get_all(cls, ado_client: AdoClient, repo_id: str, pull_request_id: str) -> list[PullRequestCommentThread]:  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/threads?api-version=7.1",
        )  # type: ignore[return-value]

@dataclass
class PullRequestComment:
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-thread-comments/list?view=azure-devops-rest-7.1
    Comments' content will be None if they've been deleted, or if they're system comments."""
    comment_id: str
    parent_comment_id: str = field(repr=False)
    content: str | None
    author: Member
    creation_date: datetime = field(repr=False)
    comment_type: CommentType
    is_deleted: bool = field(repr=False)
    liked_users: list[Member] = field(repr=False)

    def __str__(self) -> str:
        return f"PullRequestComment(id={self.comment_id}, author_email=`{self.author.email}`, content=`{self.content}`, creation_date={self.creation_date}, comment_type={self.comment_type}" + (", is_deleted=True" if self.is_deleted else "") + ")"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "PullRequestComment":
        author = Member(data["author"]["displayName"], data["author"]["uniqueName"], data["author"]["id"])
        liked_users = [Member(user["displayName"], user["uniqueName"], user["id"]) for user in data.get("usersLiked", [])]
        return cls(str(data["id"]), str(data["parentCommentId"]), data.get("content"), author, from_ado_date_string(data["publishedDate"]),
                   data.get("commentType", "regular"), data.get("isDeleted", False), liked_users)  # fmt: skip

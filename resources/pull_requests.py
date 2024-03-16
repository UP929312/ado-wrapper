from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TYPE_CHECKING
from dataclasses import dataclass, field

import requests

from utils import from_ado_date_string, DeletionFailed
from state_managed_abc import StateManagedResource
from resources.users import Member, Reviewer

if TYPE_CHECKING:
    from client import AdoClient
    from resources.repo import Repo

PullRequestStatus = Literal["active", "completed", "abandoned", "all", "notSet"]
MergeStatus = Literal["succeeded", "conflicts", "rejectedByPolicy", "rejectedByUser", "queued", "notSet"]


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
    repository: Repo
    close_date: datetime | None = field(default=None, repr=False)
    is_draft: bool = field(default=False, repr=False, metadata={"editable": True, "internal_name": "isDraft"})
    merge_status: MergeStatus = field(default="notSet")  # Static(ish)
    reviewers: list[Reviewer] = field(default_factory=list, repr=False)  # Static(ish)

    def __str__(self) -> str:
        return f"PullRequest(id={self.pull_request_id}, title={self.title}, author={self.author!s}, merge_status={self.merge_status})"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "PullRequest":
        from resources.repo import Repo  # Circular import

        member = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        reviewers = [Reviewer.from_request_payload(reviewer) for reviewer in data["reviewers"]]
        repository = Repo(data["repository"]["id"], data["repository"]["name"])
        return cls(str(data["pullRequestId"]), data["title"], data.get("description", ""), data["sourceRefName"],
                   data["targetRefName"], member, from_ado_date_string(data["creationDate"]), repository,
                   from_ado_date_string(data.get("closedDate")), data["isDraft"], data.get("mergeStatus", "notSet"), reviewers)  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, pull_request_id: str) -> "PullRequest":  # type: ignore[override]
        return super().get_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(  # type: ignore[override]
        cls, ado_client: AdoClient, repo_id: str, from_branch_name: str, pull_request_title: str, pull_request_description: str
    ) -> "PullRequest":  # fmt: skip

        payload = {"sourceRefName": f"refs/heads/{from_branch_name}", "targetRefName": "refs/heads/main", "title": pull_request_title, "description": pull_request_description}  # fmt: skip
        # "https://stackoverflow.com/questions/69097402/tf401398-the-pull-request-cannot-be-activated-because-the-source-and-or-the-tar"
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullrequests?api-version=7.1-preview.1",
            json=payload, auth=ado_client.auth,  # fmt: skip
        ).json()
        if request.get("message", "").startswith("TF401398"):
            raise ValueError("The branch you are trying to create a pull request from does not exist.")
        return cls.from_request_payload(request)

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, repo_id: str, pull_request_id: str) -> None:
        return super().delete_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}?api-version=7.1",
            pull_request_id,
        )

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def add_reviewer(self, ado_client: AdoClient, reviewer_id: str) -> None:
        return self.add_reviewer_static(ado_client, self.repository.repo_id, self.pull_request_id, reviewer_id)

    @staticmethod
    def add_reviewer_static(ado_client: AdoClient, repo_id: str, pull_request_id: str, reviewer_id: str) -> None:
        """Copy of the add_reviewer method, but static, i.e. if you have the repo id and pr id, you don't need to fetch them again"""
        request = requests.put(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/reviewers/{reviewer_id}?api-version=7.1-preview.1",
                                json={"vote": "0", "isRequired": "true"}, auth=ado_client.auth)  # fmt: skip
        assert request.status_code < 300

    def change_status(self, ado_client: AdoClient, status: PullRequestStatus) -> "PullRequest":
        request = requests.patch(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repository.repo_id}/pullRequests/{self.pull_request_id}?api-version=7.1",
            json={"status": status}, auth=ado_client.auth,  # fmt: skip
        )
        assert request.status_code < 300
        return self.__class__.from_request_payload(request.json())

    def close(self, ado_client: AdoClient) -> None:
        self.change_status(ado_client, "abandoned")

    def delete(self, ado_client: AdoClient) -> None:
        self.close(ado_client)

    def mark_as_draft(self, ado_client: AdoClient, is_draft: bool=True) -> None:
        # TODO: Make this call the self.update() method
        json_payload = {"isDraft": is_draft}
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repository.repo_id}/pullRequests/{self.pull_request_id}/draft?api-version=7.1",
            json_payload,
            auth=ado_client.auth,
        )
        assert request.status_code < 300

    def unmark_as_draft(self, ado_client: AdoClient) -> None:
        self.mark_as_draft(ado_client, False)

    def get_reviewers(self, ado_client: AdoClient) -> list[Member]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repository.repo_id}/pullRequests/{self.pull_request_id}/reviewers?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return [Member(reviewer["displayName"], reviewer["uniqueName"], reviewer["id"]) for reviewer in request["value"]]

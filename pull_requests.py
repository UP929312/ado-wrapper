from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TYPE_CHECKING

import requests

from member import Member, Reviewer
from utils import from_ado_date_string

if TYPE_CHECKING:
    from main import AdoClient
    from repository import Repo

PullRequestStatus = Literal["active", "completed", "abandoned", "all", "notSet"]
MergeStatus = Literal["succeeded", "conflicts", "rejectedByPolicy", "rejectedByUser", "queued", "notSet"]


class PullRequest:
    def __init__(self, pull_request_id: int, title: str, description: str, source_branch: str, target_branch: str, author: Member,
                 creation_date: datetime, close_date: datetime | None, is_draft: bool, repository: "Repo", merge_status: MergeStatus,
                 reviewers: list[Reviewer]) -> None:  # fmt: skip
        self.pull_request_id = pull_request_id
        self.title = title
        self.description = description
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.author = author
        self.creation_date = creation_date
        self.close_date = close_date
        self.is_draft = is_draft
        self.repository = repository
        self.merge_status = merge_status
        self.reviewers = reviewers

    def __str__(self) -> str:
        return f'PullRequest(id={self.pull_request_id}, title={self.title}, author={self.author!s}, creation_date={self.creation_date}, merge_status={self.merge_status})'

    def __repr__(self) -> str:
        return f'PullRequest(id={self.pull_request_id!r}, title={self.title!r}, description={self.description!r}, source_branch={self.source_branch!r}, target_branch={self.target_branch!r}, author={self.author!r}, creation_date={self.creation_date!s}, is_draft={self.is_draft}, merge_status={self.merge_status!r}, reviewers={self.reviewers!r})'

    @classmethod
    def from_json(cls, pr_response: dict[str, Any]) -> "PullRequest":
        from repository import Repo  # Circular import
        member = Member(pr_response["createdBy"]["displayName"], pr_response["createdBy"]["uniqueName"], pr_response["createdBy"]["id"])
        reviewers = [Reviewer.from_json(data) for data in pr_response["reviewers"]]
        repository = Repo(pr_response["repository"]["id"], pr_response["repository"]["name"])
        return cls(pr_response["pullRequestId"], pr_response["title"], pr_response.get("description", ""), pr_response["sourceRefName"],
                   pr_response["targetRefName"], member, from_ado_date_string(pr_response["creationDate"]), from_ado_date_string(pr_response.get("closedDate")),
                   pr_response["isDraft"], repository, pr_response["mergeStatus"], reviewers)

    @classmethod
    def get_by_id(cls, repo_id: str, pull_request_id: str) -> "PullRequest":
        request = requests.get(f"https://dev.azure.com/{ado_helper.ado_org}/{ado_helper.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}?api-version=7.1", auth=ado_helper.auth).json()  # fmt: skip
        return cls.from_json(request)

    @classmethod
    def create(cls, ado_helper: AdoClient, repo_id: str, branch_name: str, pull_request_title: str, pull_request_description: str) -> "PullRequest":
        payload = {"sourceRefName": branch_name, "targetRefName": "refs/heads/main", "title": pull_request_title, "description": pull_request_description}  # fmt: skip
        request = requests.post(f"https://dev.azure.com/{ado_helper.ado_org}/{ado_helper.ado_project}/_apis/git/repositories/{repo_id}/pullrequests?api-version=5.1", json=payload, auth=ado_helper.auth).json()  # fmt: skip
        return cls.from_json(request)

    def add_reviewer(self, ado_helper: AdoClient, reviewer_id: str) -> None:
        request = requests.put(f"https://dev.azure.com/{ado_helper.ado_org}/{ado_helper.ado_project}/_apis/git/repositories/{self.repository.repo_id}/pullRequests/{self.pull_request_id}/reviewers/{reviewer_id}?api-version=7.1-preview.1",
                                json={"vote": "0", "isRequired": "true"}, auth=ado_helper.auth)  # fmt: skip
        assert request.status_code < 300

    @staticmethod
    def add_reviewer_static(ado_helper: AdoClient, repo_id: str, pull_request_id: int, reviewer_id: str) -> None:
        """ Copy of the add_reviewer method, but static, i.e. if you have the repo id and pr id, you don't need to fetch them again"""
        reviewers_payload = {"vote": "0", "isRequired": "true"}
        request = requests.put(f"https://dev.azure.com/{ado_helper.ado_org}/{ado_helper.ado_project}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/reviewers/{reviewer_id}?api-version=7.1-preview.1",
                                json=reviewers_payload, auth=ado_helper.auth)  # fmt: skip
        assert request.status_code < 300

    def change_status(self, ado_helper: AdoClient, status: PullRequestStatus) -> None:
        json_payload = {"status": status}
        request = requests.post(
            f"https://dev.azure.com/{ado_helper.ado_org}/{ado_helper.ado_project}/_apis/git/repositories/{self.repository.repo_id}/pullRequests/{self.pull_request_id}?api-version=7.1",
            json=json_payload, auth=ado_helper.auth
        )
        assert request.status_code < 300

    def mark_as_draft(self, ado_helper: AdoClient) -> None:
        json_payload = {"isDraft": True}
        request = requests.post(
            f"https://dev.azure.com/{ado_helper.ado_org}/{ado_helper.ado_project}/_apis/git/repositories/{self.repository.repo_id}/pullRequests/{self.pull_request_id}/draft?api-version=7.1",
            json_payload, auth=ado_helper.auth
        )
        assert request.status_code < 300

    def get_reviewers(self, ado_helper: AdoClient) -> list[Member]:
        request = requests.get(
            f"https://dev.azure.com/{ado_helper.ado_org}/{ado_helper.ado_project}/_apis/git/repositories/{self.repository.repo_id}/pullRequests/{self.pull_request_id}/reviewers?api-version=7.1",
            auth=ado_helper.auth
        ).json()
        return [Member(reviewer["displayName"], reviewer["uniqueName"], reviewer["id"]) for reviewer in request["value"]]


if __name__ == "__main__":
    from secret import email, ado_access_token, ado_org, ado_project, EXISTING_REPO_NAME
    from main import AdoClient
    from repository import Repo
    ado_helper = AdoClient(email, ado_access_token, ado_org, ado_project)
    repo = Repo.get_by_id(ado_helper, EXISTING_REPO_NAME)
    pull_requests = repo.get_all_pull_requests(ado_helper, "all")
    print("\n".join([str(x) for x in pull_requests]))

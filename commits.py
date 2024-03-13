from typing import Literal, Any
from datetime import datetime

import requests

from client import AdoClient
from repository import Repo
from users import Member
from utils import from_ado_date_string

ChangeType = Literal["edit", "add", "delete"]
FIRST_COMMIT_ID = "0000000000000000000000000000000000000000"  # I don't know why this works, but it does, please leave it.


def get_commit_body_template(old_object_id: str | None, updates: dict[str, str], branch_name: str, change_type: ChangeType) -> dict[str, str | dict | list]:  # type: ignore[type-arg]
    return {
        "refUpdates": [
            {
                "name": f"refs/heads/{branch_name}",
                "oldObjectId": old_object_id or FIRST_COMMIT_ID,
            },
        ],
        "commits": [
            {
                "comment": "[fix]: Update links to Github SaaS",
                "changes": [
                    {
                        "changeType": change_type,
                        "item": {
                            "path": path,
                        },
                        "newContent": {
                            "content": new_content_body,
                            "contentType": "rawtext",
                        },
                    }
                    for path, new_content_body in updates.items()
                ],
            }
        ],
    }


class Commit:
    def __init__(self, commit_id: str, author: Member, date: datetime, message: str) -> None:
        self.commit_id = commit_id
        self.author = author
        self.date = date
        self.message = message

    def __str__(self) -> str:
        return f"{self.commit_id} by {self.author!s} on {self.date}\n{self.message}"

    def __repr__(self) -> str:
        return f"Commit({self.commit_id!r}, {self.author!r}, {self.date!r}, {self.message!r})"

    @classmethod
    def from_request_payload(cls, commit_response: dict[str, Any]) -> "Commit":
        member = Member(commit_response["commitId"], commit_response["author"]["name"], commit_response["author"]["email"])
        return cls(commit_response["commitId"], member, from_ado_date_string(commit_response["author"]["date"]), commit_response["comment"])

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, commit_id: str) -> "Commit":
        commit = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/commits/{commit_id}?api-version=5.1",
            auth=ado_client.auth,
        ).json()
        return cls.from_request_payload(commit)

    @classmethod
    def create(cls, ado_client: AdoClient, repo_id: str, branch_name: str, updates: dict[str, str], change_type: ChangeType) -> "Commit":
        """Creates a commit in the given repository with the given updates and returns the commit object."""
        latest_commits = requests.get(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/commits?api-version=5.1", auth=ado_client.auth).json()["value"]  # fmt: skip
        latest_commit_id = None if not latest_commits else latest_commits[0]["commitId"]
        data = get_commit_body_template(latest_commit_id, updates, branch_name, change_type)
        commit_response = requests.post(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pushes?api-version=5.1", json=data, auth=ado_client.auth).json()  # fmt: skip
        return cls.from_request_payload(commit_response["commits"][-1])

    @staticmethod
    def delete_by_id(ado_client: AdoClient, commit_id: str) -> None:
        raise NotImplementedError

    # ============ End of requirement set by all state managed resources ================== #
    #                                                                                       #
    # ============ Start of requirement set by all state managed resources ================ #

    @classmethod
    def get_all_by_repo(cls, ado_client: AdoClient, repo_id: str) -> "list[Commit]":
        """Returns a list of all commits in the given repository."""
        commits = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/commits?api-version=5.1",
            auth=ado_client.auth,
        ).json()["value"]
        print(commits[0])
        return [cls.from_request_payload(commit) for commit in commits]

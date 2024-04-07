from typing import Literal, Any
from datetime import datetime
from dataclasses import dataclass, field

import requests

from ado_wrapper.client import AdoClient
from ado_wrapper.utils import from_ado_date_string, InvalidPermissionsError
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member

ChangeType = Literal["edit", "add", "delete"]
FIRST_COMMIT_ID = "0000000000000000000000000000000000000000"  # I don't know why this works, but it does, please leave it.


def get_commit_body_template(old_object_id: str | None, updates: dict[str, str], branch_name: str, change_type: ChangeType, commit_message: str) -> dict[str, str | dict | list]:  # type: ignore[type-arg]
    return {
        "refUpdates": [
            {
                "name": f"refs/heads/{branch_name}",
                "oldObjectId": old_object_id or FIRST_COMMIT_ID,
            },
        ],
        "commits": [
            {
                "comment": commit_message,
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


@dataclass
class Commit(StateManagedResource):
    """
    https://learn.microsoft.com/en-us/rest/api/azure/devops/git/commits?view=azure-devops-rest-7.1
    https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pushes?view=azure-devops-rest-7.1
    """

    commit_id: str = field(metadata={"is_id_field": True})  # None are editable
    author: Member
    date: datetime
    message: str

    def __str__(self) -> str:
        return f"{self.commit_id} by {self.author!s} on {self.date}\n{self.message}"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Commit":
        member = Member(data["author"]["name"], data["author"]["email"], "UNKNOWN")
        return cls(data["commitId"], member, from_ado_date_string(data["author"]["date"]), data["comment"])

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, commit_id: str) -> "Commit":  # type: ignore[override]
        return super().get_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/commits/{commit_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(  # type: ignore[override]
        cls, ado_client: AdoClient, repo_id: str, from_branch_name: str, to_branch_name: str, updates: dict[str, str], change_type: ChangeType, commit_message: str,  # fmt: skip
    ) -> "Commit":
        """Creates a commit in the given repository with the given updates and returns the commit object.
        Takes a branch to get the latest commit from (and to update), and a to_branch to fork to."""
        assert not (
            from_branch_name.startswith("refs/heads/") or to_branch_name.startswith("refs/heads/")
        ), "Branch names should not start with 'refs/heads/'"
        if not updates:
            raise ValueError("No updates provided! It's not possible to create a commit without updates.")
        latest_commit = cls.get_latest_by_repo(ado_client, repo_id, from_branch_name)
        latest_commit_id = None if latest_commit is None else latest_commit.commit_id
        data = get_commit_body_template(latest_commit_id, updates, to_branch_name, change_type, commit_message)
        request = requests.post(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pushes?api-version=7.1", json=data, auth=ado_client.auth)  # fmt: skip
        if request.status_code == 400:
            raise ValueError("The commit was not created successfully, the file(s) you're trying to add might already exist there.")
        if request.status_code == 403:
            raise InvalidPermissionsError("You do not have permission to create a commit in this repo (possibly due to main branch protections)")  # fmt: skip
        if not request.json().get("commits"):
            raise ValueError("The commit was not created successfully.\nError:", request.json())
        return cls.from_request_payload(request.json()["commits"][-1])

    @staticmethod
    def delete_by_id(ado_client: AdoClient, commit_id: str) -> None:  # type: ignore[override]
        raise NotImplementedError

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_latest_by_repo(cls, ado_client: AdoClient, repo_id: str, branch_name: str | None = None) -> "Commit":
        return max(cls.get_all_by_repo(ado_client, repo_id, branch_name), key=lambda commit: commit.date)

    @classmethod
    def get_all_by_repo(cls, ado_client: AdoClient, repo_id: str, branch_name: str | None = None) -> "list[Commit]":
        """Returns a list of all commits in the given repository."""
        extra_query = (f"searchCriteria.itemVersion.version={branch_name}&searchCriteria.itemVersion.versionType={'branch'}&"
                       if branch_name is not None else "")  # fmt: skip
        return super().get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/commits?{extra_query}api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def add_initial_readme(cls, ado_client: AdoClient, repo_id: str) -> "Commit":
        default_commit_body = get_commit_body_template(None, {}, "main", "add", "")
        default_commit_body["commits"] = [{
            "comment": "Add README.md",
            "changes": [{
                "changeType": 1, "item": {"path": "/README.md"},
                "newContentTemplate": {"name": "README.md", "type": "readme"}
            }],
        }]  # fmt: skip
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/pushes?api-version=7.1",
            json=default_commit_body, auth=ado_client.auth,  # fmt: skip
        )
        return cls.from_request_payload(request.json()["commits"][0])

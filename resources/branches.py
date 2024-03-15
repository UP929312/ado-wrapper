from dataclasses import dataclass, field

import requests

from client import AdoClient
from state_managed_abc import StateManagedResource
from resources.commits import Commit


@dataclass(slots=True)
class Branch(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/refs?view=azure-devops-rest-7.1"""
    branch_id: str
    name: str = field(metadata={"editable": True})  # Maybe more?
    repo_id: str
    is_main: bool = field(default=True)
    is_protected: bool = field(default=False)
    is_deleted: bool = field(default=False)

    def __str__(self) -> str:
        return f"Branch(name={self.name}, id={self.branch_id}, is_main={self.is_main}, is_protected={self.is_protected}, is_deleted={self.is_deleted})"

    @classmethod
    def from_request_payload(cls, data: dict[str, str | bool | dict[str, str]]) -> "Branch":
        return cls(data["objectId"], data["name"], data["url"].split("/")[-2],  # type: ignore[union-attr, arg-type]
                   bool(data.get("isMain", False)), bool(data.get("isProtected", False)), bool(data.get("isDeleted")))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, branch_id: str) -> "Branch":  # type: ignore[override]
        for branch in cls.get_all_by_repo(ado_client, repo_id):
            if branch.branch_id == branch_id:
                return branch
        raise ValueError(f"Branch {branch_id} not found")

    @classmethod
    def create(cls, ado_client: AdoClient, repo_id: str, branch_name: str, source_branch: str) -> "Branch":
        Commit.create(ado_client, repo_id, source_branch, branch_name, {}, "add", "Abc")
        return cls.get_by_name(ado_client, repo_id, branch_name)

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, repo_id: str, branch_id: str) -> None:  # type: ignore[override]
        request = requests.delete(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/refs/{branch_id}?api-version=7.1",
            auth=ado_client.auth,
        )
        if request.status_code != 204:
            raise ValueError(f"Error deleting {cls.__name__} {branch_id}: {request.text}")
        assert request.status_code == 204

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all_by_repo(cls, ado_client: AdoClient, repo_id: str) -> list["Branch"]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/refs?filter=heads&api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return [cls.from_request_payload(branch) for branch in request["value"]]

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, repo_id: str, branch_name: str) -> "Branch":
        for branch in cls.get_all_by_repo(ado_client, repo_id):
            if branch.name == branch_name:
                return branch
        raise ValueError(f"Branch {branch_name} not found")

    @classmethod
    def get_main_branch(cls, ado_client: AdoClient, repo_id: str) -> "Branch":  # type: ignore[return]  # pylint: disable=inconsistent-return-statements
        for branch in cls.get_all_by_repo(ado_client, repo_id):
            if branch.is_main:
                return branch

    @classmethod
    def get_protected_branches(cls, ado_client: AdoClient, repo_id: str) -> list["Branch"]:
        return [branch for branch in cls.get_all_by_repo(ado_client, repo_id) if branch.is_protected]

    @classmethod
    def get_deleted_branches(cls, ado_client: AdoClient, repo_id: str) -> list["Branch"]:
        return [branch for branch in cls.get_all_by_repo(ado_client, repo_id) if branch.is_deleted]

    @classmethod
    def get_unprotected_branches(cls, ado_client: AdoClient, repo_id: str) -> list["Branch"]:
        return [branch for branch in cls.get_all_by_repo(ado_client, repo_id) if not branch.is_protected]

    @classmethod
    def get_active_branches(cls, ado_client: AdoClient, repo_id: str) -> list["Branch"]:
        return [branch for branch in cls.get_all_by_repo(ado_client, repo_id) if not branch.is_deleted]

    def delete(self, ado_client: AdoClient) -> None:
        self.delete_by_id(ado_client, self.repo_id, self.branch_id)

from dataclasses import dataclass, field
from typing import Literal

from ado_wrapper.client import AdoClient
from ado_wrapper.state_managed_abc import StateManagedResource

BranchEditableAttribute = Literal["name"]

@dataclass
class Branch(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/refs?view=azure-devops-rest-7.1
    This isn't entirely what I wanted, you can't branch without a commit, so I need to add a commit method to this class
    And overall, just use commits if you can.
    """

    branch_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})  # Maybe more?
    repo_id: str
    is_main: bool = True
    is_protected: bool = False
    is_deleted: bool = False

    def __str__(self) -> str:
        return f"Branch(name={self.name}, id={self.branch_id}, is_main={self.is_main}, is_protected={self.is_protected}, is_deleted={self.is_deleted})"

    @classmethod
    def from_request_payload(cls, data: dict[str, str | bool | dict[str, str]]) -> "Branch":
        return cls(data["objectId"], data["name"].removeprefix("refs/heads/"), data["url"].split("/")[-2],  # type: ignore[union-attr, arg-type]
                   bool(data.get("isMain", False)), bool(data.get("isProtected", False)), bool(data.get("isDeleted")))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, branch_id: str) -> "Branch":  # type: ignore[override]
        for branch in cls.get_all_by_repo(ado_client, repo_id):
            if branch.branch_id == branch_id:
                return branch
        raise ValueError(f"Branch {branch_id} not found")

    @classmethod
    def create(cls, ado_client: AdoClient, repo_id: str, branch_name: str, source_branch: str = "main") -> "Branch":  # type: ignore[override]
        raise NotImplementedError("You can't create a branch without a commit, use Commit.create instead")
        # Commit.create(ado_client, repo_id, source_branch, branch_name, {}, "add", "Abc")
        # return cls.get_by_name(ado_client, repo_id, branch_name)

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, repo_id: str, branch_id: str) -> None:
        return super().delete_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/refs/{branch_id}?api-version=7.1",
            branch_id,
        )

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all_by_repo(cls, ado_client: AdoClient, repo_id: str) -> list["Branch"]:
        return super().get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/refs?filter=heads&api-version=7.1",
        )  # type: ignore[return-value]

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

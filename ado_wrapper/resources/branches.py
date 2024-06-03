from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

BranchEditableAttribute = Literal["name"]


@dataclass
class Branch(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/refs?view=azure-devops-rest-7.1
    This isn't entirely what I wanted, you can't branch without a commit, so I need to add a commit method to this class
    And overall, just use commits if you can.
    """

    branch_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    repo_id: str = field(repr=False)
    creator: Member = field(repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, str | dict[str, str]]) -> Branch:
        return cls(
            str(data["objectId"]),
            data["name"].removeprefix("refs/heads/"),  # type: ignore[union-attr]
            data["url"].split("/")[-2],  # type: ignore[union-attr]
            Member.from_request_payload(data["creator"]),  # type: ignore[arg-type]
        )

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, branch_id: str) -> Branch:  # type: ignore[override]
        for branch in cls.get_all_by_repo(ado_client, repo_id):
            if branch.branch_id == branch_id:
                return branch
        raise ValueError(f"Branch {branch_id} not found")

    @classmethod
    def create(cls, ado_client: AdoClient, repo_id: str, branch_name: str, source_branch: str = "main") -> Branch:  # type: ignore[override]
        raise NotImplementedError("You can't create a branch without a commit, use Commit.create instead")

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, repo_id: str, branch_id: str) -> None:
        raise NotImplementedError("You can't delete a branch without a commit, use Commit.delete instead")
        # return super().delete_by_id(
        #     ado_client,
        #     f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/refs/{branch_id}?api-version=7.1",
        #     branch_id,
        # )

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all_by_repo(cls, ado_client: AdoClient, repo_id: str) -> list[Branch]:
        return super().get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/refs?filter=heads&api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, repo_id: str, branch_name: str) -> Branch | None:
        for branch in cls.get_all_by_repo(ado_client, repo_id):
            if branch.name == branch_name:
                return branch
        raise ValueError(f"Branch {branch_name} not found")

    @classmethod
    def get_main_branch(cls, ado_client: AdoClient, repo_id: str) -> Branch:
        return [x for x in cls.get_all_by_repo(ado_client, repo_id) if x.name in ("main", "master")][0]

    def delete(self, ado_client: AdoClient) -> None:  # Has to exist for multi-ids
        self.delete_by_id(ado_client, self.repo_id, self.branch_id)

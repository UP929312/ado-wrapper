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
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, branch_id: str) -> Branch:
        for branch in cls.get_all_by_repo(ado_client, repo_id):
            if branch.branch_id == branch_id:
                return branch
        raise ValueError(f"Branch {branch_id} not found")

    @classmethod
    def create(cls, ado_client: AdoClient, repo_id: str, branch_name: str, source_branch: str = "main") -> Branch:
        raise NotImplementedError("You can't create a branch without a commit, use Commit.create instead")

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, branch_name: str, repo_id: str) -> None:
        # https://stackoverflow.com/a/67224873
        PAYLOAD = [
            {
                "name": f"refs/heads/{branch_name}",
                "oldObjectId": cls.get_by_name(ado_client, repo_id, branch_name).branch_id,  # type: ignore[union-attr]
                "newObjectId": "0000000000000000000000000000000000000000",
            }
        ]
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/refs?api-version=7.1",
            json=PAYLOAD,
        )
        assert request.status_code == 200
        ado_client.state_manager.remove_resource_from_state("Branch", branch_name)

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all_by_repo(cls, ado_client: AdoClient, repo_name_or_id: str) -> list[Branch]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_name_or_id}/refs?filter=heads&api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, repo_name_or_id: str, branch_name: str) -> Branch | None:
        for branch in cls.get_all_by_repo(ado_client, repo_name_or_id):
            if branch.name == branch_name:
                return branch
        raise ValueError(f"Branch {branch_name} not found")

    @classmethod
    def get_main_branch(cls, ado_client: AdoClient, repo_id: str) -> Branch:
        return [x for x in cls.get_all_by_repo(ado_client, repo_id) if x.name in ("main", "master", "trunk")][0]

    def delete(self, ado_client: AdoClient) -> None:
        self.delete_by_id(ado_client, self.name, self.repo_id)

    @classmethod
    def delete_by_name(cls, ado_client: AdoClient, branch_name: str, repo_id: str) -> None:
        return cls.delete_by_id(ado_client, branch_name, repo_id)

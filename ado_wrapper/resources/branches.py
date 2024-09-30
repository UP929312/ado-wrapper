from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Any

from ado_wrapper.errors import ConfigurationError
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

FIRST_COMMIT_ID = "0000000000000000000000000000000000000000"  # This is the initial id
BranchEditableAttribute = Literal["name"]


@dataclass
class Branch(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/refs?view=azure-devops-rest-7.1
    This isn't entirely what I wanted, overall, just use commits if you can."""

    branch_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    repo_id: str = field(repr=False)
    creator: Member = field(repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Branch":
        return cls(
            str(data["objectId"]),
            data["name"].removeprefix("refs/heads/"),
            data["url"].split("/")[-2],
            Member.from_request_payload(data["creator"]),
        )

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", repo_id: str, branch_id: str) -> "Branch":
        # Can't use abstract filter because you get all by a repo
        for branch in cls.get_all_by_repo(ado_client, repo_id):
            if branch.branch_id == branch_id:
                return branch
        raise ValueError(f"Branch {branch_id} not found")

    @classmethod
    def create(cls, ado_client: "AdoClient", repo_id: str, branch_name: str, default_branch_name: str = "main") -> "Branch":
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/refs?includeLinks=false&includeStatuses=false&includeMyBranches=true&api-version=6.0-preview.1"
        ).json()["value"]
        main_branch = [x for x in request if x["name"] == f"refs/heads/{default_branch_name}"][0]
        commit_id = main_branch["objectId"]
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/refs?api-version=6.0-preview.1",
            json=[{"name": f"refs/heads/{branch_name}", "newObjectId": commit_id, "oldObjectId": FIRST_COMMIT_ID}],
        ).json()["value"][0]
        # TODO: Maybe make this use super()._create?
        return Branch(
            request["newObjectId"], branch_name, repo_id, Member.from_request_payload({"displayName": "UNKNOWN", "id": "UNKNOWN"})
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", branch_name: str, repo_id: str) -> None:
        # https://stackoverflow.com/a/67224873
        PAYLOAD = [
            {
                "name": f"refs/heads/{branch_name}",
                "oldObjectId": cls.get_by_name(ado_client, repo_id, branch_name).branch_id,  # type: ignore[union-attr]
                "newObjectId": "0000000000000000000000000000000000000000",
            }
        ]
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/refs?api-version=7.1",
            json=PAYLOAD,
        )
        if request.status_code != 200:
            raise ConfigurationError(
                f"Error, something went wrong when trying to delete that branch: {request.status_code}, {request.text}"
            )
        ado_client.state_manager.remove_resource_from_state("Branch", branch_name)

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all_by_repo(cls, ado_client: "AdoClient", repo_name_or_id: str) -> list["Branch"]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{repo_name_or_id}/refs?filter=heads&api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", repo_name_or_id: str, branch_name: str) -> "Branch | None":
        for branch in cls.get_all_by_repo(ado_client, repo_name_or_id):
            if branch.name == branch_name:
                return branch
        raise ValueError(f"Branch {branch_name} not found")

    @classmethod
    def get_main_branch(cls, ado_client: "AdoClient", repo_id: str) -> "Branch":
        return [x for x in cls.get_all_by_repo(ado_client, repo_id) if x.name in ("main", "master", "trunk")][0]

    def delete(self, ado_client: "AdoClient") -> None:
        self.delete_by_id(ado_client, self.name, self.repo_id)

    @classmethod
    def delete_by_name(cls, ado_client: "AdoClient", branch_name: str, repo_id: str) -> None:
        return cls.delete_by_id(ado_client, branch_name, repo_id)

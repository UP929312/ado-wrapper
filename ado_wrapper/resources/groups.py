from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass, field

# import requests

from ado_wrapper.state_managed_abc import StateManagedResource

# from ado_wrapper.resources.users import GroupMember

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


@dataclass
class Group(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/graph/groups?view=azure-devops-rest-7.1"""

    group_descriptor: str = field(metadata={"is_id_field": True})  # None are editable
    name: str = field(metadata={"internal_name": "displayName"})  # Not editable
    description: str
    group_id: str  # Not editable, don't use
    origin_id: str = field(metadata={"internal_name": "originId"})  # Not editable, don't use
    # group_members: list[GroupMember] = field(default_factory=list)

    def __str__(self) -> str:
        return repr(self)

    @classmethod
    def from_request_payload(cls, data: dict[str, str]) -> "Group":
        return cls(data["url"].split("/_apis/Graph/Groups/", maxsplit=1)[1], data["displayName"], data.get("description", ""),
                   data["domain"].removeprefix("vstfs:///Classification/TeamProject/"), data["originId"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, group_descriptor: str) -> "Group":
        return super().get_by_id(
            ado_client,  # Preview required
            f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/graph/groups/{group_descriptor}?api-version=7.1-preview.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(cls, ado_client: AdoClient, name: str) -> "Group":  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, group_id: str) -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["Group"]:  # type: ignore[override]
        return super().get_all(
            ado_client,  # Preview required
            f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/graph/groups?api-version=7.1-preview.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, group_name: str) -> "Group":
        for group in cls.get_all(ado_client):
            if group.name == group_name:
                return group
        raise ValueError(f"Group {group_name} not found")

    # def get_members(self, ado_client: AdoClient) -> list["GroupMember"]:
    #     request = requests.get(
    #         f"https://dev.azure.com/{ado_client.ado_org}/_apis/projects/{ado_client.ado_project}/groups/{self.group_id}/members?api-version=7.1-preview.2",
    #         auth=ado_client.auth,
    #     ).json()
    #     rint(request)
    #     # return [GroupMember.from_request_payload(member) for member in request]

    def delete(self, ado_client: AdoClient, group_id: str) -> None:
        self.delete_by_id(ado_client, group_id)

    @classmethod
    def get_all_by_member(cls, ado_client: AdoClient, member_descriptor_id: str) -> list["Group"]:
        raise NotImplementedError
        # Will finish this later
        # return [group for group in cls.get_all(ado_client) if group.group_descriptor == member_descriptor_id]

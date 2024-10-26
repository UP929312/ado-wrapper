from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ado_wrapper.state_managed_abc import StateManagedResource

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


@dataclass
class Group(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/graph/groups?view=azure-devops-rest-7.1"""

    group_descriptor: str = field(metadata={"is_id_field": True})  # None are editable
    name: str = field(metadata={"internal_name": "displayName"})  # Not editable
    description: str
    domain: str
    origin_id: str = field(metadata={"internal_name": "originId"})  # Not editable
    # group_members: list[GroupMember] = field(default_factory=list)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Group":
        return cls(data["url"].split("/_apis/Graph/Groups/", maxsplit=1)[1], data["displayName"], data.get("description", ""),
                   data["domain"].removeprefix("vstfs:///Classification/TeamProject/"), data["originId"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", group_descriptor: str) -> "Group":
        return super()._get_by_url(
            ado_client,  # Preview required
            f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/graph/groups/{group_descriptor}?api-version=7.1-preview.1",
        )

    @classmethod
    def create(cls, ado_client: "AdoClient", name: str, description: str = "ado_wrapper created group") -> "Group":
        return super()._create(
            ado_client,
            f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/graph/groups?api-version=7.1-preview.1",
            payload={"displayName": name, "description": description, "specialType": "Generic"},
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", group_descriptor: str) -> None:
        return super()._delete_by_id(
            ado_client,
            f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/graph/groups/{group_descriptor}?api-version=7.1-preview.1",
            group_descriptor,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["Group"]:
        return super()._get_all(
            ado_client,  # Preview required
            f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/graph/groups?api-version=7.1-preview.1",
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/permissions?subjectDescriptor={self.group_descriptor}"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", group_name: str) -> "Group | None":
        return cls._get_by_abstract_filter(ado_client, lambda group: group.name == group_name)

    # @classmethod
    # def get_all_by_member(cls, ado_client: "AdoClient", member_descriptor_id: str) -> list["Group"]:
    #     raise NotImplementedError
    # Will finish this later
    # return [group for group in cls.get_all(ado_client) if group.group_descriptor == member_descriptor_id]

    # def get_members(self, ado_client: "AdoClient") -> list["GroupMember"]:
    #     request = ado_client.session.get(
    #         f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/projects/{ado_client.ado_project_name}/groups/{self.group_id}/members?api-version=7.1-preview.2",
    #     ).json()
    #     rint(request)
    #     # return [GroupMember.from_request_payload(member) for member in request]

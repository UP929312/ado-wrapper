from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ado_wrapper.resources.users import Member
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


@dataclass
class SecureFile(StateManagedResource):
    security_file_id: str = field(metadata={"is_id_field": True})
    name: str
    created_on: datetime
    created_by: Member
    modified_by: Member
    modified_on: datetime | None = None

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "SecureFile":
        created_by = Member.from_request_payload(data["createdBy"])
        modified_by = Member.from_request_payload(data["modifiedBy"])
        return cls(str(data["id"]), data["name"], from_ado_date_string(data["createdOn"]), created_by,
                   modified_by, from_ado_date_string(data.get("modifiedOn")))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", secure_file_id: str) -> "SecureFile":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/securefiles/{secure_file_id}?api-version=7.1-preview.1"
        )  # pyright: ignore[reportReturnType]

    # @classmethod
    # def create(cls, ado_client: "AdoClient", name: str, file: dict[str, str]) -> "SecureFile":
    #     payload = {
    #         "name": name,
    #         # "variables": variables,
    #         "type": "Vsts",
    #     }
    #     # TODO: We use data for the payload, not json, so we cannot use _create, but still want state management...
    #     return super()._create(
    #         ado_client,
    #         f"/{ado_client.ado_project_name}/_apis/distributedtask/securefiles?name={name}&api-version=7.1",
    #         payload,
    #     )  # pyright: ignore[reportReturnType]

    # @classmethod
    # def delete_by_id(cls, ado_client: "AdoClient", variable_group_id: str) -> None:
    #     requires_initialisation(ado_client)
    #     return super()._delete_by_id(
    #         ado_client,
    #         f"/_apis/distributedtask/variablegroups/{variable_group_id}?projectIds={ado_client.ado_project_id}&api-version=7.1",
    #         variable_group_id,
    #     )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["SecureFile"]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/securefiles?api-version=7.1-preview.1",
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_library?itemType=SecureFiles&view=SecureFileView&secureFileId={self.security_file_id}"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "SecureFile | None":
        return cls._get_by_abstract_filter(ado_client, lambda variable_group: variable_group.name == name)

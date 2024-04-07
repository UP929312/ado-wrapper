from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING, Literal
from dataclasses import dataclass, field

from ado_wrapper.utils import from_ado_date_string
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

VariableGroupEditableAttribute = Literal["variables"]


@dataclass
class VariableGroup(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/variablegroups?view=azure-devops-rest-7.1"""

    variable_group_id: str = field(metadata={"is_id_field": True})
    name: str  # Cannot currently change the name of a variable group
    description: str  # = field(metadata={"editable": True})  # Bug in the api means this is not editable (it never returns or sets description)
    variables: dict[str, str] = field(metadata={"editable": True})
    created_on: datetime
    created_by: Member
    modified_by: Member
    modified_on: datetime | None = None

    def __str__(self) -> str:
        return repr(self)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "VariableGroup":
        created_by = Member(data["createdBy"]["displayName"], "UNKNOWN", data["createdBy"]["id"])
        modified_by = Member(data["modifiedBy"]["displayName"], "UNKNOWN", data["modifiedBy"]["id"])
        return cls(str(data["id"]), data["name"], data.get("description", ""),
                   {key: value["value"] if isinstance(value, dict) else value for key, value in data["variables"].items()},
                   from_ado_date_string(data["createdOn"]), created_by, modified_by, from_ado_date_string(data.get("modifiedOn")))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, variable_group_id: str) -> "VariableGroup":
        return super().get_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/variablegroups/{variable_group_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(  # type: ignore[override]
        cls, ado_client: AdoClient, variable_group_name: str, variable_group_description: str, variables: dict[str, str]  # fmt: skip
    ) -> "VariableGroup":
        payload = {
            "name": variable_group_name,
            "description": variable_group_description,
            "variables": variables,
            "type": "Vsts",
            "variableGroupProjectReferences": [
                {
                    "description": variable_group_description,
                    "name": variable_group_name,
                    "projectReference": {"id": ado_client.ado_project_id, "name": ado_client.ado_project},
                }
            ],
        }
        return super().create(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/variablegroups?api-version=7.1",
            payload,
        )  # type: ignore[return-value]

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, variable_group_id: str) -> None:  # type: ignore[override]
        return super().delete_by_id(
            ado_client,
            f"/_apis/distributedtask/variablegroups/{variable_group_id}?projectIds={ado_client.ado_project_id}&api-version=7.1",
            variable_group_id,
        )

    def update(self, ado_client: AdoClient, attribute_name: VariableGroupEditableAttribute, attribute_value: Any) -> None:  # type: ignore[override]
        # WARNING: This method works 80-90% of the time, for some reason, it fails randomly, ADO API is at fault.
        params = {
            "variableGroupProjectReferences": [{"name": self.name, "projectReference": {"id": ado_client.ado_project_id}}],
             "id": self.variable_group_id, "name": self.name, "type": "Vsts", "variables": self.variables  # fmt: skip
        }
        super().update(
            ado_client, "put",
            f"/_apis/distributedtask/variablegroups/{self.variable_group_id}?api-version=7.1",
            attribute_name, attribute_value, params  # fmt: skip
        )

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["VariableGroup"]:  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/variablegroups?api-version=7.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def delete(self, ado_client: AdoClient) -> None:
        self.delete_by_id(ado_client, self.variable_group_id)

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, name: str) -> "VariableGroup | None":
        for variable_group in cls.get_all(ado_client):
            if variable_group.name == name:
                return variable_group
        return None

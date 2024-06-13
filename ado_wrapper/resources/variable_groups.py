from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.resources.users import Member
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string, requires_initialisation

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

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> VariableGroup:
        # print("\n", data)
        created_by = Member.from_request_payload(data["createdBy"])
        modified_by = Member.from_request_payload(data["modifiedBy"])
        return cls(str(data["id"]), data["name"], data.get("description", ""),
                   {key: value["value"] if isinstance(value, dict) else value for key, value in data["variables"].items()},
                   from_ado_date_string(data["createdOn"]), created_by, modified_by, from_ado_date_string(data.get("modifiedOn")))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, variable_group_id: str) -> VariableGroup:
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/variablegroups/{variable_group_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(
        cls, ado_client: AdoClient, variable_group_name: str, variable_group_description: str, variables: dict[str, str]  # fmt: skip
    ) -> VariableGroup:
        payload = {
            "name": variable_group_name,
            "variables": variables,
            "type": "Vsts",
            "variableGroupProjectReferences": [
                {
                    "description": variable_group_description,
                    "name": variable_group_name,
                    "projectReference": {"name": ado_client.ado_project},
                }
            ],
        }
        return super()._create(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/variablegroups?api-version=7.1",
            payload,
        )  # type: ignore[return-value]

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, variable_group_id: str) -> None:
        requires_initialisation(ado_client)
        return super()._delete_by_id(
            ado_client,
            f"/_apis/distributedtask/variablegroups/{variable_group_id}?projectIds={ado_client.ado_project_id}&api-version=7.1",
            variable_group_id,
        )

    def update(self, ado_client: AdoClient, attribute_name: VariableGroupEditableAttribute, attribute_value: Any) -> None:
        # WARNING: This method works 80-90% of the time, for some reason, it fails randomly, ADO API is at fault.
        params = {
            "variableGroupProjectReferences": [{"name": self.name, "projectReference": {"name": ado_client.ado_project}}],
            "name": self.name, "variables": self.variables  # fmt: skip
        }
        super()._update(
            ado_client, "put",
            f"/_apis/distributedtask/variablegroups/{self.variable_group_id}?api-version=7.1",
            attribute_name, attribute_value, params  # fmt: skip
        )

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list[VariableGroup]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/variablegroups?api-version=7.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, name: str) -> VariableGroup | None:
        return cls._get_by_abstract_filter(ado_client, lambda variable_group: variable_group.name == name)  # type: ignore[return-value, attr-defined]

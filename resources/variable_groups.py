from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING
from dataclasses import dataclass, field

import requests

from utils import from_ado_date_string, DeletionFailed
from state_managed_abc import StateManagedResource
from resources.users import Member

if TYPE_CHECKING:
    from client import AdoClient


@dataclass(slots=True)
class VariableGroup(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/variablegroups?view=azure-devops-rest-7.1"""

    variable_group_id: str = field(metadata={"is_id_field": True})
    name: str = field(repr=True, metadata={"editable": True})
    description: str = field(repr=True, metadata={"editable": True})
    variables: dict[str, str]
    created_on: datetime
    created_by: Member
    modified_by: Member
    modified_on: datetime | None = field(default=None)

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
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/distributedtask/variablegroups?groupIds={variable_group_id}&api-version=7.1-preview.2",
            auth=ado_client.auth,
        ).json()["value"][0]  # fmt: skip
        return cls.from_request_payload(request)

    @classmethod
    def create(cls, ado_client: AdoClient, variable_group_name: str, variable_group_description: str, variables: dict[str, str]) -> "VariableGroup":  # fmt: skip
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
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/distributedtask/variablegroups?api-version=7.1-preview.2",
            json=payload, auth=ado_client.auth,  # fmt: skip
        ).json()
        resource = cls.from_request_payload(request)
        ado_client.add_resource_to_state(cls.__name__, resource.variable_group_id, resource.to_json())  # type: ignore[arg-type]
        return resource

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, variable_group_id: str) -> None:
        request = requests.delete(
            f"https://dev.azure.com/{ado_client.ado_org}/_apis/distributedtask/variablegroups/{variable_group_id}?projectIds={ado_client.ado_project_id}&api-version=7.1-preview.2",
            auth=ado_client.auth,
        )
        if request.status_code != 204:
            raise DeletionFailed(f"Error deleting {cls.__name__} {variable_group_id}: {request.text}")
        ado_client.remove_resource_from_state(cls.__name__, variable_group_id)  # type: ignore[arg-type]

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

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["VariableGroup"]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/distributedtask/variablegroups?api-version=7.1-preview.2",
            auth=ado_client.auth,
        ).json()["value"]  # fmt: skip
        return [cls.from_request_payload(variable_group) for variable_group in request]

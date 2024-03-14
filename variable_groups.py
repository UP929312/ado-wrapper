from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

import requests

from users import Member
from utils import from_ado_date_string
from state_managed_abc import StateManagedResource

if TYPE_CHECKING:
    from client import AdoClient


class VariableGroup(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/variablegroups?view=azure-devops-rest-7.1"""
    def __init__(self, variable_group_id: str, name: str, description: str, variables: dict[str, str], created_on: datetime,
                 created_by: Member, modified_by: Member, modified_on: datetime | None) -> None:  # fmt: skip
        self.variable_group_id = variable_group_id
        self.name = name
        self.description = description
        self.variables = variables
        self.created_on = created_on
        self.created_by = created_by
        self.modified_by = modified_by
        self.modified_on = modified_on

    def __str__(self) -> str:
        return f"VariableGroup(id={self.variable_group_id}, name={self.name}, created_by={self.created_by}, created_on={self.created_on}, modified_by={self.modified_by}, modified_on={self.modified_on}, variables={self.variables})"

    def __repr__(self) -> str:
        return f"VariableGroup(id={self.variable_group_id!r}, name={self.name!r}, description={self.description!r}, variables={self.variables!r}, created_on={self.created_on!s}, created_by={self.created_by!r}, modified_by={self.modified_by!r}, modified_on={self.modified_on!s})"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "VariableGroup":
        return cls(data["id"], data["name"], data["description"], data["variables"], from_ado_date_string(data["created_on"]),
                   Member(data["created_by"]["displayName"], data["created_by"]["uniqueName"], data["created_by"]["id"]),
                   Member(data["modified_by"]["displayName"], data["modified_by"]["uniqueName"], data["modified_by"]["id"]),
                   from_ado_date_string(data["modified_on"]))  # fmt: skip

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.variable_group_id,
            "name": self.name,
            "description": self.description,
            "variables": self.variables,
            "created_on": self.created_on.isoformat(),
            "created_by": self.created_by.to_json(),
            "modified_by": self.modified_by.to_json(),
            "modified_on": self.modified_on.isoformat() if self.modified_on else None,
        }

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "VariableGroup":
        created_by = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        modified_by = Member(data["modifiedBy"]["displayName"], data["modifiedBy"]["uniqueName"], data["modifiedBy"]["id"])
        return cls(str(data["id"]), data["name"], data.get("description", ""),
                   {key: value["value"] if isinstance(value, dict) else value for key, value in data["variables"].items()},
                   from_ado_date_string(data["createdOn"]), created_by, modified_by, from_ado_date_string(data.get("modifiedOn")))  # fmt: skip

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["VariableGroup"]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/distributedtask/variablegroups?api-version=7.1-preview.2",
            auth=ado_client.auth,
        ).json()["value"]  # fmt: skip
        return [cls.from_request_payload(variable_group) for variable_group in request]

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, variable_group_id: str) -> "VariableGroup":
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/distributedtask/variablegroups?groupIds={variable_group_id}&api-version=7.1-preview.2",
            auth=ado_client.auth,
        ).json()["value"][0]  # fmt: skip
        return cls.from_request_payload(request)

    @classmethod
    def create(cls, ado_client: AdoClient, repo_id: str, branch_name: str, pull_request_title: str, pull_request_description: str) -> "VariableGroup":  # fmt: skip
        raise NotImplementedError

    @staticmethod
    def delete_by_id(ado_client: AdoClient, variable_group_id: str) -> None:
        raise NotImplementedError

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def delete(self, ado_client: AdoClient) -> None:
        self.delete_by_id(ado_client, self.variable_group_id)

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, name: str) -> "VariableGroup":
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/distributedtask/variablegroups?groupName={name}&api-version=7.1-preview.2",
            auth=ado_client.auth,
        ).json()["value"][0]  # fmt: skip
        return cls.from_request_payload(request)

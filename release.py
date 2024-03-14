from datetime import datetime
from typing import Any, Literal

import requests

from client import AdoClient
from users import Member
from utils import from_ado_date_string, to_iso, from_iso, ResourceNotFound

ReleaseStatus = Literal["active", "abandoned", "draft", "undefined"]

# ========================================================================================================
# WARNING: THIS FILE IS MAINLY UNTESTED, AND MAY NOT WORK AS EXPECTED
# FEEL FREE TO MAKE A PR TO FIX/IMPROVE THIS FILE
# ========================================================================================================


def get_release_definition(name: str, variable_group_ids: list[int] | None, agent_pool_id: int) -> dict[str, Any]:
    return {
        "id": 0,
        "name": name,
        "variableGroups": variable_group_ids or [],
        "path": "\\",
        "releaseNameFormat": "Release-$(rev: r)",
        "environments": [
            {
                "name": "Stage 1",
                "retentionPolicy": {
                    "daysToKeep": 30,
                    "releasesToKeep": 3,
                    "retainBuild": True,
                },
                "preDeployApprovals": {
                    "approvals": [
                        {
                            "rank": 1,
                            "isAutomated": True,
                            "isNotificationOn": False,
                        }
                    ],
                },
                "postDeployApprovals": {
                    "approvals": [
                        {
                            "rank": 1,
                            "isAutomated": True,
                            "isNotificationOn": False,
                        }
                    ],
                },
                "deployPhases": [
                    {
                        "deploymentInput": {
                            "queueId": agent_pool_id,
                            "enableAccessToken": False,
                            "timeoutInMinutes": 0,
                            "jobCancelTimeoutInMinutes": 1,
                            "condition": "succeeded()",
                        },
                        "rank": 1,
                        "phaseType": 1,
                        "name": "Agent job",
                    }
                ],
            }
        ],
    }


# ========================================================================================================


class Release:
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/releases?view=azure-devops-rest-7.1"""
    def __init__(self, release_id: str, name: str, status: ReleaseStatus, created_on: datetime, created_by: Member, description: str,
                 variables: list[dict[str, Any]] | None, variable_groups: list[int] | None, keep_forever: bool) -> None:  # fmt: skip
        self.release_id = release_id  # Static
        self.name = name  # Static
        self.status = status  # Static
        self.created_on = created_on  # Static
        self.created_by = created_by  # Static
        self.description = description  # Static
        self.variables = variables or []  # Static
        self.variable_groups = variable_groups or []  # Static
        self.keep_forever = keep_forever  # Static

    def __str__(self) -> str:
        return f"{self.name} ({self.release_id}), {self.status}"

    def __repr__(self) -> str:
        return (
            f"Release(id={self.release_id}, name={self.name}, status={self.status}, created_on={self.created_on}, "
            f"created_by={self.created_by!r}, description={self.description})"
        )

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Release":
        created_by = Member.from_json(data["created_by"])
        return cls(data["release_id"], data["name"], data["status"], from_iso(data["created_on"]), created_by, data["description"],
                   data["variables"], data["variable_groups"], data["keep_forever"])  # fmt: skip

    def to_json(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "name": self.name,
            "status": self.status,
            "created_on": to_iso(self.created_on),
            "created_by": self.created_by.to_json(),
            "description": self.description,
            "variables": self.variables,
            "variable_groups": self.variable_groups,
            "keep_forever": self.keep_forever,
        }

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Release":
        created_by = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        return cls(data["id"], data["name"], data["status"], from_ado_date_string(data["createdOn"]), created_by, data["description"],
                   data.get("variables", None), data.get("variableGroups", None), data["keepForever"])  # fmt: skip

    @classmethod  # TODO: Test
    def get_by_id(cls, ado_client: AdoClient, release_id: int) -> "Release":
        request = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases/{release_id}?api-version=7.1",
            auth=ado_client.auth,
        )
        if request.status_code == 404:
            raise ResourceNotFound(f"The {cls.__name__} with id {release_id} could not be found!")
        return cls.from_request_payload(request.json())

    @classmethod  # TODO: Test
    def create(cls, ado_client: AdoClient, definition_id: int) -> "Release":
        body = {"definitionId": definition_id, "description": "An automated release created by ADO-API"}
        request = requests.post(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1", json=body, auth=ado_client.auth  # fmt: skip
        ).json()
        return cls.from_request_payload(request)

    @staticmethod  # TODO: Test
    def delete_by_id(ado_client: AdoClient, release_id: str) -> None:  # TODO: Test
        delete_request = requests.delete(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases/{release_id}?api-version=7.1", auth=ado_client.auth  # fmt: skip
        )
        assert delete_request.status_code == 204

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def delete(self, ado_client: AdoClient) -> None:  # TODO: Test
        self.delete_by_id(ado_client, self.release_id)

    @classmethod  # TODO: Test
    def get_all(cls, ado_client: AdoClient, definition_id: int) -> "list[Release]":
        response = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1&definitionId={definition_id}", auth=ado_client.auth  # fmt: skip
        ).json()
        return [cls.from_request_payload(release) for release in response["value"]]


# ========================================================================================================


class ReleaseDefinition:
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/definitions?view=azure-devops-rest-7.1"""
    def __init__(self, name: str, description: str, created_by: Member, created_on: datetime, release_definition_id: int, release_name_format: str,
                 variable_groups: list[int], variables: list[dict[str, Any]] | None = None):  # fmt: skip
        self.name = name
        self.description = description
        self.created_by = created_by  # Static
        self.created_on = created_on  # Static
        self.release_definition_id = release_definition_id  # Static
        self.release_name_format = release_name_format
        self.variable_groups = variable_groups
        self.variables = variables or []

    def __str__(self) -> str:
        return f"{self.name}, {self.description}, created by {self.created_by}, created on {self.created_on!s}"

    def __repr__(self) -> str:
        return (
            f"ReleaseDefinition(name={self.name!r}, description={self.description!r}, created_by={self.created_by!r}, "
            f"created_on={self.created_on!s}, id={self.release_definition_id}, release_name_format={self.release_name_format!r}, "
            f"variable_groups={self.variable_groups!r}, variables={self.variables!r})"
        )

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ReleaseDefinition":
        created_by = Member.from_json(data["created_by"])
        return cls(data["name"], data["description"], created_by, from_iso(data["created_on"]), data["release_definition_id"],
                   data["release_name_format"], data["variable_groups"], data["variables"])  # fmt: skip

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by.to_json(),
            "created_on": to_iso(self.created_on),
            "release_definition_id": self.release_definition_id,
            "release_name_format": self.release_name_format,
            "variable_groups": self.variable_groups,
            "variables": self.variables,
        }

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ReleaseDefinition":
        created_by = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        return cls(data["name"], data["releases"], created_by, from_ado_date_string(data["createdOn"]), data["id"],
                   data["releaseNameFormat"], data["variableGroups"], data.get("variables", None))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, release_id: int) -> "ReleaseDefinition":
        response = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions/{release_id}?api-version=7.0",
            auth=ado_client.auth,
        ).json()
        return cls.from_request_payload(response)

    @classmethod
    def get_all_releases_for_definition(cls, ado_client: AdoClient, definition_id: int) -> "list[Release]":
        response = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1&definitionId={definition_id}",
            auth=ado_client.auth,
        ).json()
        return [Release.from_request_payload(release) for release in response["value"]]

    @classmethod  # TODO: Test
    def create(cls, ado_client: AdoClient, name: str, variable_group_ids: list[int] | None, agent_pool_id: int) -> "ReleaseDefinition":
        """Takes a list of variable group ids to include, and an agent_pool_id"""
        body = get_release_definition(name, variable_group_ids, agent_pool_id)
        data = requests.post(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions?api-version=7.0",
            json=body,
            auth=ado_client.auth,
        ).json()
        return cls.from_request_payload(data)

    def delete(self, ado_client: AdoClient) -> None:  # TODO: Test
        delete_request = requests.delete(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions/{self.release_definition_id}?forceDelete=true&api-version=7.1",
            auth=ado_client.auth,
        )
        assert delete_request.status_code == 204


# ========================================================================================================

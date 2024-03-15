from datetime import datetime
from typing import Any, Literal
from dataclasses import dataclass, field

import requests

from client import AdoClient
from state_managed_abc import StateManagedResource
from utils import DeletionFailed, from_ado_date_string, ResourceNotFound
from resources.users import Member

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


@dataclass(slots=True)
class Release(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/releases?view=azure-devops-rest-7.1"""

    release_id: str
    name: str
    status: ReleaseStatus
    created_on: datetime
    created_by: Member
    description: str
    variables: list[dict[str, Any]] | None = field(default_factory=list, repr=False)  # type: ignore[assignment]
    variable_groups: list[int] | None = field(default_factory=list, repr=False)  # type: ignore[assignment]
    keep_forever: bool = field(default=False, repr=False)

    def __str__(self) -> str:
        return f"{self.name} ({self.release_id}), {self.status}"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Release":
        created_by = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        return cls(data["id"], data["name"], data["status"], from_ado_date_string(data["createdOn"]), created_by, data["description"],
                   data.get("variables", None), data.get("variableGroups", None), data["keepForever"])  # fmt: skip

    @classmethod  # TODO: Test
    def get_by_id(cls, ado_client: AdoClient, release_id: str) -> "Release":
        request = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases/{release_id}?api-version=7.1",
            auth=ado_client.auth,
        )
        if request.status_code == 404:
            raise ResourceNotFound(f"The {cls.__name__} with id {release_id} could not be found!")
        return cls.from_request_payload(request.json())

    @classmethod  # TODO: Test
    def create(cls, ado_client: AdoClient, definition_id: str) -> "Release":
        body = {"definitionId": definition_id, "description": "An automated release created by ADO-API"}
        request = requests.post(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1", json=body, auth=ado_client.auth  # fmt: skip
        ).json()
        return cls.from_request_payload(request)

    @classmethod  # TODO: Test
    def delete_by_id(cls, ado_client: AdoClient, release_id: str) -> None:  # TODO: Test
        delete_request = requests.delete(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases/{release_id}?api-version=7.1", auth=ado_client.auth  # fmt: skip
        )
        if delete_request.status_code != 204:
            raise DeletionFailed(f"Error deleting {cls.__name__} {release_id}: {delete_request.text}")
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


@dataclass(slots=True)
class ReleaseDefinition(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/definitions?view=azure-devops-rest-7.1"""

    release_definition_id: int
    name: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True})
    created_by: Member
    created_on: datetime
    release_name_format: str = field(metadata={"editable": True})
    variable_groups: list[int] = field(metadata={"editable": True})
    variables: list[dict[str, Any]] | None = field(default_factory=list, repr=False)  # type: ignore[assignment]

    def __str__(self) -> str:
        return f"{self.name}, {self.description}, created by {self.created_by}, created on {self.created_on!s}"

    def __repr__(self) -> str:
        return (
            f"ReleaseDefinition(name={self.name!r}, description={self.description!r}, created_by={self.created_by!r}, "
            f"created_on={self.created_on!s}, id={self.release_definition_id}, release_name_format={self.release_name_format!r}, "
            f"variable_groups={self.variable_groups!r}, variables={self.variables!r})"
        )

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ReleaseDefinition":
        created_by = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        return cls(data["id"], data["name"], data["description"], created_by, from_ado_date_string(data["createdOn"]),
                   data["releaseNameFormat"], data["variableGroups"], data.get("variables", None))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, release_id: str) -> "ReleaseDefinition":
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

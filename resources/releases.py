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


@dataclass
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
        return super().get_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases/{release_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod  # TODO: Test
    def create(cls, ado_client: AdoClient, definition_id: str) -> "Release":  # type: ignore[override]
        return super().create(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1",
            {"definitionId": definition_id, "description": "An automated release created by ADO-API"},
        )  # type: ignore[return-value]

    @classmethod  # TODO: Test
    def delete_by_id(cls, ado_client: AdoClient, release_id: str) -> None:  # type: ignore[override]
        return super().delete_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases/{release_id}?api-version=7.1",
            release_id,
        )

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


@dataclass
class ReleaseDefinition(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/definitions?view=azure-devops-rest-7.1"""

    release_definition_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True})
    created_by: Member
    created_on: datetime
    release_name_format: str = field(metadata={"editable": True, "internal_name": "releaseNameFormat"})
    variable_groups: list[int] = field(metadata={"editable": True, "internal_name": "variableGroups"})
    variables: list[dict[str, Any]] | None = field(default_factory=list, repr=False)  # type: ignore[assignment]

    def __str__(self) -> str:
        return f"{self.name}, {self.description}, created by {self.created_by}, created on {self.created_on!s}"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ReleaseDefinition":
        created_by = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        return cls(data["id"], data["name"], data["description"], created_by, from_ado_date_string(data["createdOn"]),
                   data["releaseNameFormat"], data["variableGroups"], data.get("variables", None))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, release_id: str) -> "ReleaseDefinition":
        return super().get_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions/{release_id}?api-version=7.0",
        )  # type: ignore[return-value]

    @classmethod  # TODO: Test
    def create(cls, ado_client: AdoClient, name: str, variable_group_ids: list[int] | None, agent_pool_id: int) -> "ReleaseDefinition":  # type: ignore[override]
        """Takes a list of variable group ids to include, and an agent_pool_id"""
        return super().create(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions?api-version=7.0",
            get_release_definition(name, variable_group_ids, agent_pool_id),
        )  # type: ignore[return-value]

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, release_definition_id: str) -> None:  # type: ignore[override]
        return super().delete_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions/{release_definition_id}?forceDelete=true&api-version=7.1",
            release_definition_id,
        )

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def delete(self, ado_client: AdoClient) -> None:  # TODO: Test
        return self.delete_by_id(ado_client, self.release_definition_id)

    @classmethod
    def get_all_releases_for_definition(cls, ado_client: AdoClient, definition_id: int) -> "list[Release]":
        response = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1&definitionId={definition_id}",
            auth=ado_client.auth,
        ).json()
        return [Release.from_request_payload(release) for release in response["value"]]


# ========================================================================================================

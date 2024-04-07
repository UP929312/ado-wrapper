from datetime import datetime
from typing import Any, Literal
from dataclasses import dataclass, field

import requests

from ado_wrapper.client import AdoClient
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string
from ado_wrapper.resources.users import Member

ReleaseDefinitionEditableAttribute = Literal["name", "description", "release_name_format", "variable_groups"]
ReleaseStatus = Literal["active", "abandoned", "draft", "undefined"]

# ========================================================================================================
# WARNING: THIS FILE IS MAINLY UNTESTED, AND MAY NOT WORK AS EXPECTED
# FEEL FREE TO MAKE A PR TO FIX/IMPROVE THIS FILE
# ========================================================================================================


def get_release_definition(
    ado_client: AdoClient, name: str, variable_group_ids: list[int], agent_pool_id: str, revision: str = "1", _id: str = ""
) -> dict[str, Any]:
    return {
        "name": name,
        "id": _id,
        "variableGroups": variable_group_ids,
        "path": "\\",
        "releaseNameFormat": "Release-$(rev: r)",
        "revision": int(revision),
        "modifiedOn": datetime.now().isoformat(),
        "environments": [
            {
                "name": "Stage 1",
                "preDeployApprovals": {
                    "approvals": [
                        {
                            "rank": 1,
                            "isAutomated": False,
                            "isNotificationOn": False,
                            "id": 0,
                            "approver": {
                                "id": ado_client.pat_author.origin_id,
                                "displayName": "Automated",
                            },
                        }
                    ]
                },
                "postDeployApprovals": {
                    "approvals": [
                        {
                            "rank": 1,
                            "isAutomated": True,
                            "isNotificationOn": False,
                            "id": 0,
                        }
                    ]
                },
                "deployPhases": [
                    {
                        "rank": 1,
                        "phaseType": "agentBasedDeployment",
                        "name": "Run on agent",
                        "workflowTasks": [],
                        "deploymentInput": {
                            "parallelExecution": {"parallelExecutionType": "none"},
                            "skipArtifactsDownload": False,
                            "queueId": agent_pool_id,
                            "demands": [],
                            "enableAccessToken": False,
                            "timeoutInMinutes": 0,
                            "jobCancelTimeoutInMinutes": 1,
                            "condition": "succeeded()",
                            "overrideInputs": {},
                        },
                    }
                ],
                "retentionPolicy": {"daysToKeep": 30, "releasesToKeep": 3, "retainBuild": True},
            }
        ],
    }


# ========================================================================================================


@dataclass
class Release(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/releases?view=azure-devops-rest-7.1"""

    release_id: str = field(metadata={"is_id_field": True})
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

    @classmethod  # TO-DO: Test
    def get_by_id(cls, ado_client: AdoClient, release_id: str) -> "Release":
        return super().get_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases/{release_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod  # TO-DO: Test
    def create(cls, ado_client: AdoClient, definition_id: str, description: str = "Made with the ado_wrapper Python library") -> "Release":  # type: ignore[override]
        return super().create(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1",
            {"definitionId": definition_id, "description": description},
        )  # type: ignore[return-value]

    @classmethod  # TO-DO: Test
    def delete_by_id(cls, ado_client: AdoClient, release_id: str) -> None:  # type: ignore[override]
        return super().delete_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases/{release_id}?api-version=7.1",
            release_id,
        )

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def delete(self, ado_client: AdoClient) -> None:
        self.delete_by_id(ado_client, self.release_id)

    @classmethod
    def get_all(cls, ado_client: AdoClient, definition_id: str) -> "list[Release]":  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1&definitionId={definition_id}",
        )  # type: ignore[return-value]


# ========================================================================================================


@dataclass
class ReleaseDefinition(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/definitions?view=azure-devops-rest-7.1"""

    release_definition_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True})
    created_by: Member
    created_on: datetime
    # modified_by: Member  # Could be added later on
    # modified_on: datetime  # Could be added later on
    # path: str  # Could be added later on
    # tags: list[str]  # Could be added later on
    release_name_format: str = field(metadata={"editable": True, "internal_name": "releaseNameFormat"})
    variable_group_ids: list[int]  # = field(metadata={"editable": True, "internal_name": "variableGroups"})
    is_disabled: bool = field(default=False, repr=False)  # , metadata={"editable": True, "internal_name": "isDisabled"})
    variables: dict[str, Any] | None = field(default_factory=dict, repr=False)  # type: ignore[assignment]
    environments: list[dict[str, Any]] = field(default_factory=list, repr=False)
    _agent_pool_id: str = field(default="1")
    revision: str = field(default="1")
    _raw_data: dict[str, Any] = field(default_factory=dict, repr=False)  # Used in update, don't use this directly

    def __str__(self) -> str:
        return f'ReleaseDefinition(name="{self.name}", description="{self.description}", created_by={self.created_by!r}, created_on={self.created_on!s}'

    @property
    def agent_pool_id(self) -> str:
        if self._agent_pool_id == "1":
            raise ValueError("No agent pool id has been found! Cannot do this operation!")
        return self._agent_pool_id

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ReleaseDefinition":
        created_by = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        return cls(str(data["id"]), data["name"], data.get("description") or "", created_by, from_ado_date_string(data["createdOn"]),
                   data["releaseNameFormat"], data["variableGroups"], data.get("isDeleted", False), data.get("variables", None),
                   data.get("environments", []), data.get("environments", [{"deployPhases": [{"deploymentInput": {"queueId": "1"}}]}]
                            )[0]["deployPhases"][0]["deploymentInput"]["queueId"], data.get("revision", "1"), data)  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, release_definition_id: str) -> "ReleaseDefinition":
        return super().get_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions/{release_definition_id}?api-version=7.0",
        )  # type: ignore[return-value]

    @classmethod
    def create(cls, ado_client: AdoClient, name: str, variable_group_ids: list[int], agent_pool_id: str) -> "ReleaseDefinition":  # type: ignore[override]
        """Takes a list of variable group ids to include, and an agent_pool_id"""
        return super().create(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions?api-version=7.0",
            get_release_definition(ado_client, name, variable_group_ids, agent_pool_id),
        )  # type: ignore[return-value]

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, release_definition_id: str) -> None:  # type: ignore[override]
        for release in ReleaseDefinition.get_all_releases_for_definition(ado_client, release_definition_id):
            release.delete(ado_client)
        return super().delete_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions/{release_definition_id}?forceDelete=True&api-version=7.1",
            release_definition_id,
        )

    def update(self, ado_client: AdoClient, attribute_name: ReleaseDefinitionEditableAttribute, attribute_value: Any) -> None:  # type: ignore[override]
        self.revision = str(int(self.revision) + 1)
        return super().update(
            ado_client, "put",
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions/{self.release_definition_id}?api-version=7.1",
            attribute_name, attribute_value, self._raw_data,  # fmt: skip
        )

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def delete(self, ado_client: AdoClient) -> None:
        return self.delete_by_id(ado_client, self.release_definition_id)

    @classmethod
    def get_all_releases_for_definition(cls, ado_client: AdoClient, definition_id: str) -> "list[Release]":
        response = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1&definitionId={definition_id}",
            auth=ado_client.auth,
        ).json()
        return [Release.from_request_payload(release) for release in response["value"]]

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> "list[ReleaseDefinition]":  # type: ignore[override]
        response = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions?api-version=7.1",
            auth=ado_client.auth,
        ).json()["value"]
        return [cls.from_request_payload(data) for data in response]


# ========================================================================================================

# @dataclass
# class ReleaseEnvironment:
#     """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/definitions/list?view=azure-devops-rest-7.1&tabs=HTTP#releasedefinitionenvironment"""
#     release_environment_id: str = field(metadata={"is_id_field": True})
#     name: str = field(metadata={"editable": True})
#     rank: str = field(metadata={"editable": True})
#     variables: dict[str, Any] = field(default_factory=dict, repr=False, metadata={"editable": True})
#     variable_groups: list[int] = field(default_factory=list, repr=False, metadata={"editable": True})

from datetime import datetime
from typing import Any, Literal
from dataclasses import dataclass, field

import requests

from client import AdoClient
from state_managed_abc import StateManagedResource
from utils import from_ado_date_string
from resources.users import Member

ReleaseStatus = Literal["active", "abandoned", "draft", "undefined"]

# ========================================================================================================
# WARNING: THIS FILE IS MAINLY UNTESTED, AND MAY NOT WORK AS EXPECTED
# FEEL FREE TO MAKE A PR TO FIX/IMPROVE THIS FILE
# ========================================================================================================


def get_release_definition(name: str, variable_group_ids: list[int] | None, agent_pool_id: str) -> dict[str, Any]:
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
    def get_all(cls, ado_client: AdoClient, definition_id: str) -> "list[Release]":  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1&definitionId={definition_id}",
        )  # type: ignore[return-value]


# ========================================================================================================

"""
artifacts': [],
    'triggers': [],
    'properties': {'DefinitionCreationSource': {'$type': 'System.String', '$value': 'ReleaseNew'},"
"""

@dataclass
class ReleaseDefinition(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/definitions?view=azure-devops-rest-7.1"""

    release_definition_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True})
    created_by: Member
    created_on: datetime
    # modified_by: Member  # Meh
    # modified_on: datetime  # Meh
    # path: str  # Meh
    # tags: list[str]
    release_name_format: str = field(metadata={"editable": True, "internal_name": "releaseNameFormat"})
    variable_groups: list[int] = field(metadata={"editable": True, "internal_name": "variableGroups"})
    is_disabled: bool = field(default=False, repr=False, metadata={"editable": True, "internal_name": "isDisabled"})
    variables: dict[str, Any] | None = field(default_factory=dict, repr=False)  # type: ignore[assignment]

    def __str__(self) -> str:
        return f"ReleaseDefinition(name=\"{self.name}\", description=\"{self.description}\", created_by={self.created_by!r}, created_on={self.created_on!s}"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ReleaseDefinition":
        created_by = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        return cls(data["id"], data["name"], data["description"], created_by, from_ado_date_string(data["createdOn"]),
                   data["releaseNameFormat"], data["variableGroups"], data.get("isDeleted", False), data.get("variables", None))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, release_definition_id: str) -> "ReleaseDefinition":
        return super().get_by_id(
            ado_client,
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions/{release_definition_id}?api-version=7.0",
        )  # type: ignore[return-value]

    @classmethod  # TODO: Test
    def create(cls, ado_client: AdoClient, name: str, variable_group_ids: list[int] | None, agent_pool_id: str) -> "ReleaseDefinition":  # type: ignore[override]
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
    def get_all_releases_for_definition(cls, ado_client: AdoClient, definition_id: str) -> "list[Release]":
        response = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/releases?api-version=7.1&definitionId={definition_id}",
            auth=ado_client.auth,
        ).json()
        return [Release.from_request_payload(release) for release in response["value"]]

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> "list[ReleaseDefinition]":  # type: ignore[override]
        response = requests.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/release/definitions?api-version=7.1-preview.4",
            auth=ado_client.auth,
        ).json()["value"]
        return [cls.from_request_payload(data) for data in response]

# ========================================================================================================

#"""
# environments=[
#     {'id': 9, 'name': 'Stage 1', 'rank': 1, 'variables': {}, 'variableGroups': [], 
#     'preDeployApprovals': {'approvals': [{'rank': 1, 'isAutomated': True, 'isNotificationOn': False, 'id': 26}], 'approvalOptions': {'requiredApproverCount': None, 'releaseCreatorCanBeApprover': False, 'autoTriggeredAndPreviousEnvironmentApprovedCanBeSkipped': False, 'enforceIdentityRevalidation': False, 'timeoutInMinutes': 0, 'executionOrder': 'beforeGates'}},
#     'deployStep': {'id': 29},
#     'postDeployApprovals': {'approvals': [{'rank': 1, 'isAutomated': True, 'isNotificationOn': False, 'id': 30}], 'approvalOptions': {'requiredApproverCount': None, 'releaseCreatorCanBeApprover': False, 'autoTriggeredAndPreviousEnvironmentApprovedCanBeSkipped': False, 'enforceIdentityRevalidation': False, 'timeoutInMinutes': 0, 'executionOrder': 'afterSuccessfulGates'}},
#     'deployPhases': [{'deploymentInput': {'parallelExecution': {'parallelExecutionType': 'none'}, 'agentSpecification': None, 'skipArtifactsDownload': False, 'artifactsDownloadInput': {'downloadInputs': []}, 'queueId': 31, 'demands': [], 'enableAccessToken': False, 'timeoutInMinutes': 0, 'jobCancelTimeoutInMinutes': 1, 'condition': 'succeeded()', 'overrideInputs': {}}, 'rank': 1, 'phaseType': 'agentBasedDeployment', 'name': 'Agent job', 'refName': None, 'workflowTasks': []}],
#     'environmentOptions': {'emailNotificationType': 'OnlyOnFailure', 'emailRecipients': 'release.environment.owner;release.creator', 'skipArtifactsDownload': False, 'timeoutInMinutes': 0, 'enableAccessToken': False, 'publishDeploymentStatus': True, 'badgeEnabled': False, 'autoLinkWorkItems': False, 'pullRequestDeploymentEnabled': False},
#     'demands': [],
#     'conditions': [{'name': 'ReleaseStarted', 'conditionType': 'event', 'value': '', 'result': None}],
#     'executionPolicy': {'concurrencyCount': 1, 'queueDepthCount': 0},
#     'schedules': [],
#     'currentRelease': {'id': 0, 'url': 'https://vsrm.dev.azure.com/VFCloudEngineering/1d88f59f-723d-44eb-b97a-57e48d410848/_apis/Release/releases/0', '_links': {}},
#     'retentionPolicy': {'daysToKeep': 30, 'releasesToKeep': 3, 'retainBuild': True},
#     'processParameters': {},
#     'properties': {'BoardsEnvironmentType': {'$type': 'System.String', '$value': 'unmapped'}, 'LinkBoardsWorkItems': {'$type': 'System.String', '$value': 'False'}},
#     'preDeploymentGates': {'id': 0, 'gatesOptions': None, 'gates': []},
#     'postDeploymentGates': {'id': 0, 'gatesOptions': None, 'gates': []},
#     'environmentTriggers': [],
#     'badgeUrl': 'https://vsrm.dev.azure.com/VFCloudEngineering/_apis/public/Release/badge/1d88f59f-723d-44eb-b97a-57e48d410848/9/9'},
    
#     {'id': 10, 'name': 'Stage 2', 'rank': 2, 'owner': {'displayName': 'Ben Skerritt', 'url': 'https://spsprodweu5.vssps.visualstudio.com/A6b7eafe0-46f5-4363-b3be-9c99ddedc97b/_apis/Identities/09615253-ea52-637f-b8e4-63cab674eac7', '_links': {'avatar': {'href': 'https://dev.azure.com/VFCloudEngineering/_apis/GraphProfile/MemberAvatars/aad.MDk2MTUyNTMtZWE1Mi03MzdmLWI4ZTQtNjNjYWI2NzRlYWM3'}}, 'id': '09615253-ea52-637f-b8e4-63cab674eac7', 'uniqueName': 'ben.skerritt@vodafone.com', 'imageUrl': 'https://dev.azure.com/VFCloudEngineering/_apis/GraphProfile/MemberAvatars/aad.MDk2MTUyNTMtZWE1Mi03MzdmLWI4ZTQtNjNjYWI2NzRlYWM3', 'descriptor': 'aad.MDk2MTUyNTMtZWE1Mi03MzdmLWI4ZTQtNjNjYWI2NzRlYWM3'}, 'variables': {}, 'variableGroups': [], 'preDeployApprovals': {'approvals': [{'rank': 1, 'isAutomated': True, 'isNotificationOn': False, 'id': 27}], 'approvalOptions': {'requiredApproverCount': None, 'releaseCreatorCanBeApprover': False, 'autoTriggeredAndPreviousEnvironmentApprovedCanBeSkipped': False, 'enforceIdentityRevalidation': False, 'timeoutInMinutes': 0, 'executionOrder': 'beforeGates'}}, 'deployStep': {'id': 28}, 'postDeployApprovals': {'approvals': [{'rank': 1, 'isAutomated': True, 'isNotificationOn': False, 'id': 31}], 'approvalOptions': {'requiredApproverCount': None, 'releaseCreatorCanBeApprover': False, 'autoTriggeredAndPreviousEnvironmentApprovedCanBeSkipped': False, 'enforceIdentityRevalidation': False, 'timeoutInMinutes': 0, 'executionOrder': 'afterSuccessfulGates'}}, 'deployPhases': [{'deploymentInput': {'parallelExecution': {'parallelExecutionType': 'none'}, 'agentSpecification': None, 'skipArtifactsDownload': False, 'artifactsDownloadInput': {'downloadInputs': []}, 'queueId': 31, 'demands': [], 'enableAccessToken': False, 'timeoutInMinutes': 0, 'jobCancelTimeoutInMinutes': 1, 'condition': 'succeeded()', 'overrideInputs': {}}, 'rank': 1, 'phaseType': 'agentBasedDeployment', 'name': 'Agent job', 'refName': None, 'workflowTasks': []}], 'environmentOptions': {'emailNotificationType': 'OnlyOnFailure', 'emailRecipients': 'release.environment.owner;release.creator', 'skipArtifactsDownload': False, 'timeoutInMinutes': 0, 'enableAccessToken': False, 'publishDeploymentStatus': True, 'badgeEnabled': False, 'autoLinkWorkItems': False, 'pullRequestDeploymentEnabled': False}, 'demands': [], 'conditions': [{'name': 'Stage 1', 'conditionType': 'environmentState', 'value': '4', 'result': None}], 'executionPolicy': {'concurrencyCount': 1, 'queueDepthCount': 0}, 'schedules': [], 'currentRelease': {'id': 0, 'url': 'https://vsrm.dev.azure.com/VFCloudEngineering/1d88f59f-723d-44eb-b97a-57e48d410848/_apis/Release/releases/0', '_links': {}}, 'retentionPolicy': {'daysToKeep': 30, 'releasesToKeep': 3, 'retainBuild': True}, 'processParameters': {}, 'properties': {'BoardsEnvironmentType': {'$type': 'System.String', '$value': 'unmapped'}, 'LinkBoardsWorkItems': {'$type': 'System.String', '$value': 'False'}}, 'preDeploymentGates': {'id': 0, 'gatesOptions': None, 'gates': []}, 'postDeploymentGates': {'id': 0, 'gatesOptions': None, 'gates': []}, 'environmentTriggers': [], 'badgeUrl': 'https://vsrm.dev.azure.com/VFCloudEngineering/_apis/public/Release/badge/1d88f59f-723d-44eb-b97a-57e48d410848/9/10'}],

# #"""

# @dataclass
# class ReleaseEnvironment:
#     """https://learn.microsoft.com/en-us/rest/api/azure/devops/release/definitions/list?view=azure-devops-rest-7.1&tabs=HTTP#releasedefinitionenvironment"""
#     release_environment_id: str = field(metadata={"is_id_field": True})
#     name: str = field(metadata={"editable": True})
#     rank: str = field(metadata={"editable": True})
#     variables: dict[str, Any] = field(default_factory=dict, repr=False, metadata={"editable": True})
#     variable_groups: list[int] = field(default_factory=list, repr=False, metadata={"editable": True})

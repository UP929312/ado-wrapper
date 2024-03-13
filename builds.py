from datetime import datetime
from typing import Any, Literal

import requests

from client import AdoClient
from members import Member
from repository import Repo
from utils import from_ado_date_string

BuildStatus = Literal["notStarted", "inProgress", "completed", "cancelling", "postponed", "notSet", "none"]
QueuePriority = Literal["low", "belowNormal", "normal", "aboveNormal", "high"]

# ========================================================================================================


def get_build_definition(name: str, repo_id: str, repo_name: str, path_to_pipeline: str) -> dict[str, Any]:
    return {
        "folder": None,
        "name": f"{name}",
        "configuration": {
            "type": "yaml",
            "path": path_to_pipeline,
            "repository": {"id": repo_id, "name": repo_name, "type": "azureReposGit"},
        },
    }


# ========================================================================================================


class Build:
    def __init__(self, build_id: str, build_number: str, status: BuildStatus, requested_by: Member, repository: Repo,
                 parameters: dict[str, str], start_time: datetime, finish_time: datetime, queue_time: datetime, reason: str,
                 priority: QueuePriority) -> None:  # fmt: skip
        self.build_id = build_id
        self.build_number = build_number
        self.status = status
        self.requested_by = requested_by
        self.repository = repository
        self.parameters = parameters
        self.start_time = start_time
        self.finish_time = finish_time
        self.queue_time = queue_time
        self.reason = reason
        self.priority = priority

    def __str__(self) -> str:
        return f"{self.build_number} ({self.build_id}), {self.status}"

    def __repr__(self) -> str:
        return (
            f"Build(id={self.build_id}, name={self.build_number}, status={self.status}, requested_by={self.requested_by},"
            f"start_time={self.start_time}, finish_time={self.finish_time}), reason={self.reason}, priority={self.priority})"
        )

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Build":
        requested_by = Member(data["requestedBy"]["displayName"], data["requestedBy"]["uniqueName"], data["requestedBy"]["id"])
        repo = Repo(data["repository"]["id"], data["repository"]["name"])
        return cls(data["id"], data["buildNumber"], data["status"], requested_by, repo, data["templateParameters"],
                   from_ado_date_string(data["startTime"]), from_ado_date_string(data["finishTime"]),
                   from_ado_date_string(data["queueTime"]), data["reason"], data["priority"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, build_id: int) -> "Build":
        response = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds/{build_id}?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return cls.from_json(response)

    @classmethod
    def get_all_builds_by_definition(cls, ado_client: AdoClient, definition_id: int) -> "list[Build]":
        response = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds?api-version=7.1&definitions={definition_id}",
            auth=ado_client.auth,
        ).json()
        return [cls.from_json(build) for build in response["value"]]


#     @classmethod  # TODO: Test
#     def created(cls, ado_client: AdoHelper, definition_id: int) -> "Build":
#         body = {"definitionId": definition_id, "description": "An automated build created by ADO-Cleanup"}
#         request = requests.post(f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds?api-version=7.1", json=body, auth=ado_client.auth).json()
#         return cls.from_json(request)

#     def delete(self) -> None:  # TODO: Test
#         delete_request = requests.delete(
#             f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds/{self.id}?api-version=7.1", auth=ado_client.auth
#         )
#         assert delete_request.status_code == 204

# ========================================================================================================


class BuildDefinition:
    def __init__(self, build_definition_id: str, name: str, description: str, path: str, created_by: Member, created_date: datetime, repo: Repo,
                 variables: dict[str, str] | None, variable_groups: list[int] | None) -> None:  # fmt: skip
        self.build_definition_id = build_definition_id
        self.name = name
        self.description = description
        self.path = path
        self.created_by = created_by
        self.created_date = created_date
        self.repo = repo
        self.variables = variables or {}  # Kept in for reporting
        self.variable_groups = variable_groups or []  # Kept in for reporting

    def __str__(self) -> str:
        return f"{self.name}, {self.build_definition_id}, created by {self.created_by}, created on {self.created_date!s}"

    def __repr__(self) -> str:
        return f"BuildDefinition(name={self.name!r}, description={self.description}, created_by={self.created_by!r}, created_on={self.created_date!s}, id={self.build_definition_id}, repo={self.repo!r})"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "BuildDefinition":
        created_by = Member(data["authoredBy"]["displayName"], data["authoredBy"]["uniqueName"], data["authoredBy"]["id"])
        repo = Repo(data["repository"]["id"], data["repository"]["name"])
        return cls(data["id"], data["name"], data.get("description", ""), data["process"]["yamlFilename"], created_by,
                   from_ado_date_string(data["createdDate"]), repo, data.get("variables", None), data.get("variableGroups", None))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, build_definition_id: int) -> "BuildDefinition":
        response = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions/{build_definition_id}?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return cls.from_json(response)

    def get_all_builds_by_definition(self, ado_client: AdoClient) -> "list[Build]":  # TODO: Test
        response = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds?api-version=7.1&definitions={self.build_definition_id}",
            auth=ado_client.auth,
        ).json()
        return [Build.from_json(build) for build in response["value"]]

    # @classmethod  # TODO: Test
    # def create(cls, ado_client: AdoHelper, name: str, repo_id: str, repo_name: str, path_to_pipeline: str) -> "BuildDefinition":
    #     """Takes a list of variable group ids to include, and an agent_pool_id"""
    #     body = get_build_definition(name, repo_id, repo_name, path_to_pipeline)
    #     data = requests.post(
    #         f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions?api-version=7.0",
    #         json=body, auth=ado_client.auth,
    #     ).json()
    #     return cls.from_json(data)

    # def delete(self) -> None:  # TODO: Test
    #     delete_request = requests.delete(
    #         f"https://vsrm.dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions/{self.id}?forceDelete=true&api-version=7.1", auth=ado_client.auth
    #     )
    #     assert delete_request.status_code == 204


# ========================================================================================================

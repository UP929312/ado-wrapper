from datetime import datetime
from typing import Any, Literal

import requests

from client import AdoClient
from users import Member
from repository import Repo
from utils import from_ado_date_string, from_iso, to_iso, DeletionFailed
from state_managed_abc import StateManagedResource

BuildStatus = Literal["notStarted", "inProgress", "completed", "cancelling", "postponed", "notSet", "none"]
QueuePriority = Literal["low", "belowNormal", "normal", "aboveNormal", "high"]

# ========================================================================================================


def get_build_definition(
    name: str, repo_id: str, repo_name: str, path_to_pipeline: str, description: str, project: str, agent_pool_id: str
) -> dict[str, Any]:
    return {
        "name": f"{name}",
        "description": description,
        "repository": {"id": repo_id, "name": repo_name, "type": "TfsGit"},
        "project": project,
        "process": {
            "yamlFilename": path_to_pipeline,
            "type": 2,
        },
        "type": "build",
        "queue": {"id": agent_pool_id},
    }


# ========================================================================================================


class Build(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds?view=azure-devops-rest-7.1"""
    def __init__(self, build_id: str, build_number: str, status: BuildStatus, requested_by: Member, repository: Repo,
                 parameters: dict[str, str], start_time: datetime | None, finish_time: datetime | None, queue_time: datetime | None, reason: str,
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
        requested_by = Member.from_json(data["requested_by"])
        repo = Repo.from_json(data["repository"])
        return cls(data["build_id"], data["build_number"], data["status"], requested_by, repo, data["parameters"],
                   data["start_time"], from_iso(data["finish_time"]), from_iso(data["queue_time"]), data["reason"], data["priority"])  # fmt: skip

    def to_json(self) -> dict[str, Any]:
        return {
            "build_id": self.build_id,
            "build_number": self.build_number,
            "status": self.status,
            "requested_by": self.requested_by.to_json(),
            "repository": self.repository.to_json(),
            "parameters": self.parameters,
            "start_time": to_iso(self.start_time),
            "finish_time": to_iso(self.finish_time),
            "queue_time": to_iso(self.queue_time),
            "reason": self.reason,
            "priority": self.priority,
        }

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Build":
        requested_by = Member(data["requestedBy"]["displayName"], data["requestedBy"]["uniqueName"], data["requestedBy"]["id"])
        repo = Repo(data["repository"]["id"], data["repository"]["name"])
        return cls(str(data["id"]), str(data["buildNumber"]), data["status"], requested_by, repo, data.get("templateParameters", {}),
                   from_ado_date_string(data.get("startTime")), from_ado_date_string(data.get("finishTime")),
                   from_ado_date_string(data.get("queueTime")), data["reason"], data["priority"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, build_id: str) -> "Build":
        response = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds/{build_id}?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return cls.from_request_payload(response)

    @classmethod
    def create(cls, ado_client: AdoClient, definition_id: str) -> "Build":
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds?definitionId={definition_id}&api-version=7.1",
            json={"reason": "An automated build created by the ADO-API"}, auth=ado_client.auth,  # fmt: skip
        ).json()
        return cls.from_request_payload(request)

    @staticmethod
    def delete_by_id(ado_client: AdoClient, build_id: str) -> None:
        delete_request = requests.delete(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds/{build_id}?api-version=7.1",
            auth=ado_client.auth,
        )
        assert delete_request.status_code == 204

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all_by_definition(cls, ado_client: AdoClient, definition_id: str) -> "list[Build]":
        response = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds?api-version=7.1&definitions={definition_id}",
            auth=ado_client.auth,
        ).json()["value"]
        return [cls.from_request_payload(build) for build in response]

    def delete(self, ado_client: AdoClient) -> None:
        return self.delete_by_id(ado_client, self.build_id)


# ========================================================================================================


class BuildDefinition(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions?view=azure-devops-rest-7.1"""
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

    def to_json(self) -> dict[str, Any]:
        return {
            "build_definition_id": self.build_definition_id,
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "created_by": self.created_by.to_json(),
            "created_date": self.created_date.isoformat(),
            "repo": self.repo.to_json(),
            "variables": self.variables,
            "variable_groups": self.variable_groups,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "BuildDefinition":
        created_by = Member.from_json(data["created_by"])
        repo = Repo.from_json(data["repo"])
        return cls(data["build_definition_id"], data["name"], data["description"], data["path"], created_by,
                    datetime.fromisoformat(data["created_date"]), repo, data.get("variables", None), data.get("variable_groups", None))  # fmt: skip

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildDefinition":
        """Creates a build definition object from the response payload of a request to the ADO API. Repo is not always present"""
        created_by = Member(data["authoredBy"]["displayName"], data["authoredBy"]["uniqueName"], data["authoredBy"]["id"])
        repo = Repo(data.get("repository", {"id": "UNKNOWN"})["id"], data.get("repository", {"name": "UNKNOWN"})["name"])
        return cls(str(data["id"]), data["name"], data.get("description", ""), data.get("process", {"yamlFilename": "UNKNOWN"})["yamlFilename"], created_by,
                   from_ado_date_string(data["createdDate"]), repo, data.get("variables", None), data.get("variableGroups", None))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, build_definition_id: str) -> "BuildDefinition":
        response = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions/{build_definition_id}?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return cls.from_request_payload(response)

    @classmethod
    def create(
        cls, ado_client: AdoClient, name: str, repo_id: str, repo_name: str, path_to_pipeline: str, description: str, agent_pool_id: str
    ) -> "BuildDefinition":
        """Takes a list of variable group ids to include, and an agent_pool_id"""
        body = get_build_definition(name, repo_id, repo_name, path_to_pipeline, description, ado_client.ado_project, agent_pool_id)
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions?api-version=7.0",
            json=body,
            auth=ado_client.auth,
        ).json()
        ado_client.add_resource_to_state(cls.__name__, request["id"], request)  # type: ignore[arg-type]
        return cls.from_request_payload(request)

    @staticmethod
    def delete_by_id(ado_client: AdoClient, resource_id: str) -> None:
        request = requests.delete(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions/{resource_id}?forceDelete=true&api-version=7.1",
            auth=ado_client.auth,
        )
        if request.status_code != 204:
            raise DeletionFailed(f"Failed to delete build definition with id {resource_id}")
        ado_client.remove_resource_from_state(BuildDefinition.__name__, resource_id)  # type: ignore[arg-type]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def get_all_builds_by_definition(self, ado_client: AdoClient) -> "list[Build]":
        return Build.get_all_by_definition(ado_client, self.build_definition_id)

    @classmethod
    def get_all_by_repo_id(cls, ado_client: AdoClient, repo_id: str) -> "list[BuildDefinition]":
        response = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions?repositoryId={repo_id}&repositoryType={'TfsGit'}&api-version=7.1",
            auth=ado_client.auth,
        ).json()["value"]
        return [cls.from_request_payload(build) for build in response]

    def delete(self, ado_client: AdoClient) -> None:
        return self.delete_by_id(ado_client, self.build_definition_id)


# ========================================================================================================

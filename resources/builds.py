from datetime import datetime
from typing import Any, Literal
from dataclasses import dataclass, field
import time

import requests

from client import AdoClient
from utils import from_ado_date_string
from state_managed_abc import StateManagedResource
from resources.users import Member
from resources.repo import BuildRepository

BuildStatus = Literal["notStarted", "inProgress", "completed", "cancelling", "postponed", "notSet", "none"]
QueuePriority = Literal["low", "belowNormal", "normal", "aboveNormal", "high"]

# ========================================================================================================


def get_build_definition(
    name: str, repo_id: str, repo_name: str, path_to_pipeline: str, description: str, project: str, agent_pool_id: str, branch_name: str = "main"  # fmt: skip
) -> dict[str, Any]:
    return {
        "name": f"{name}",
        "description": description,
        "repository": {
            "id": repo_id,
            "name": repo_name,
            "type": "TfsGit",
            "defaultBranch": f"refs/heads/{branch_name}",
        },
        "project": project,
        "process": {
            "yamlFilename": path_to_pipeline,
            "type": 2,
        },
        "type": "build",
        "queue": {"id": agent_pool_id},
    }


# ========================================================================================================


@dataclass
class Build(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds?view=azure-devops-rest-7.1"""

    build_id: str
    build_number: str
    status: BuildStatus
    requested_by: Member
    build_repo: BuildRepository
    parameters: dict[str, str]
    definition: "BuildDefinition | None" = field(repr=False)
    start_time: datetime | None = field(default=None)
    finish_time: datetime | None = field(default=None)
    queue_time: datetime | None = field(default=None)
    reason: str = field(default="An automated build created by the ADO-API")
    priority: QueuePriority = field(default="normal")

    def __str__(self) -> str:
        return f"{self.build_number} ({self.build_id}), {self.status}"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Build":
        requested_by = Member(data["requestedBy"]["displayName"], data["requestedBy"]["uniqueName"], data["requestedBy"]["id"])
        build_repo = BuildRepository.from_request_payload(data["repository"])
        build_definition = BuildDefinition.from_request_payload(data["definition"]) if "definition" in data else None
        return cls(str(data["id"]), str(data["buildNumber"]), data["status"], requested_by, build_repo, data.get("templateParameters", {}),
                   build_definition, from_ado_date_string(data.get("startTime")), from_ado_date_string(data.get("finishTime")),
                   from_ado_date_string(data.get("queueTime")), data["reason"], data["priority"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, build_id: str) -> "Build":
        return super().get_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds/{build_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(cls, ado_client: AdoClient, definition_id: str, source_branch: str = "refs/heads/main") -> "Build":  # type: ignore[override]
        return super().create(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds?definitionId={definition_id}&api-version=7.1",
            {"reason": "An automated build created by the ADO-API", "sourceBranch": source_branch},
        )  # type: ignore[return-value]

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, build_id: str) -> None:  # type: ignore[override]
        cls.delete_all_leases(ado_client, build_id)
        return super().delete_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds/{build_id}?api-version=7.1",
            build_id,
        )

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

    @classmethod
    def create_and_wait_until_completion(cls, ado_client: AdoClient, definition_id: str, branch_name: str = "main", max_timeout_seconds: int = 300) -> "Build":  # fmt: skip
        """Creates a build and waits until it is completed, or raises a TimeoutError if it takes too long.
        WARNING: This is a blocking operation, it will not return until the build is completed or the timeout is reached."""
        build = cls.create(ado_client, definition_id, branch_name)
        start_time = datetime.now()
        while True:
            build = Build.get_by_id(ado_client, build.build_id)
            if build.status == "completed":
                break
            if (datetime.now() - start_time).seconds > max_timeout_seconds:
                raise TimeoutError(f"The build did not complete within {max_timeout_seconds} seconds ({max_timeout_seconds//60} minutes)")
            time.sleep(3)
        return build

    @staticmethod
    def delete_all_leases(ado_client: AdoClient, build_id: str) -> None:
        leases = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds/{build_id}/leases?api-version=7.1-preview.1",
            auth=ado_client.auth,
        ).json()["value"]
        for lease in leases:
            lease_response = requests.delete(
                f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/retention/leases?ids={lease['leaseId']}&api-version=6.1",
                auth=ado_client.auth,
            )
            assert lease_response.status_code <= 204


# ========================================================================================================


@dataclass
class BuildDefinition(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions?view=azure-devops-rest-7.1"""

    build_definition_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True})
    path: str
    created_by: Member | None
    created_date: datetime | None
    build_repo: BuildRepository | None = field(repr=False)
    revision: str = field(default="1")
    variables: dict[str, str] | None = field(default_factory=dict, repr=False)  # type: ignore[assignment]
    variable_groups: list[int] | None = field(default_factory=list, repr=False)  # type: ignore[assignment]

    def __str__(self) -> str:
        return f"{self.name}, {self.build_definition_id}, created by {self.created_by}, created on {self.created_date!s}"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildDefinition":
        """Repo is not always present, Member is sometimes present, sometimes None"""
        created_by = (
            Member(data["authoredBy"]["displayName"], data["authoredBy"]["uniqueName"], data["authoredBy"]["id"])
            if "authoredBy" in data else None
        )  # fmt: skip
        build_repository = BuildRepository.from_request_payload(data["repository"]) if "repository" in data else None
        return cls(str(data["id"]), data["name"], data.get("description", ""), data.get("process", {"yamlFilename": "UNKNOWN"})["yamlFilename"], created_by,
                from_ado_date_string(data.get("createdDate")), build_repository, str(data["revision"]), data.get("variables", None), data.get("variableGroups", None))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, build_definition_id: str) -> "BuildDefinition":
        return super().get_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions/{build_definition_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(  # type: ignore[override]
        cls, ado_client: AdoClient, name: str, repo_id: str, repo_name: str, path_to_pipeline: str, description: str, agent_pool_id: str, branch_name: str = "main",  # fmt: skip
    ) -> "BuildDefinition":
        return super().create(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions?api-version=7.0",
            payload=get_build_definition(
                name, repo_id, repo_name, path_to_pipeline, description, ado_client.ado_project, agent_pool_id, branch_name
            ),
        )  # type: ignore[return-value]

    def update(self, ado_client: AdoClient, attribute_name: str, attribute_value: Any) -> None:  # type: ignore[override]
        return super().update(
            ado_client, "put",
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions/{self.build_definition_id}?api-version=7.1-preview.7",
            {attribute_name: attribute_value, "revision": int(self.revision)+1}, attribute_name, attribute_value,  # fmt: skip
        )


    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, resource_id: str) -> None:  # type: ignore[override]
        builds = Build.get_all_by_definition(ado_client, resource_id)
        for build in builds:
            build.delete(ado_client)
        return super().delete_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions/{resource_id}?forceDelete=true&api-version=7.1",
            resource_id,
        )

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

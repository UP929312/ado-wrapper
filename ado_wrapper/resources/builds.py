import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.resources.environment import Environment, PipelineAuthorisation
from ado_wrapper.resources.repo import BuildRepository
from ado_wrapper.resources.users import Member
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

BuildDefinitionEditableAttribute = Literal["name", "description"]
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

    build_id: str = field(metadata={"is_id_field": True})
    build_number: str
    status: BuildStatus = field(metadata={"editable": True})  # Only this is editable ):
    requested_by: Member = field(repr=False)
    build_repo: BuildRepository = field(repr=False)
    parameters: dict[str, str] = field(repr=False)
    definition: "BuildDefinition | None" = field(repr=False)
    start_time: datetime | None = field(repr=False)
    finish_time: datetime | None = field(repr=False)
    queue_time: datetime | None = field(repr=False, default=None)
    reason: str = field(default="An automated build created with the ado_wrapper Python library", repr=False)
    priority: QueuePriority = field(default="normal", repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Build":
        requested_by = Member.from_request_payload(data["requestedBy"])
        build_repo = BuildRepository.from_request_payload(data["repository"])
        build_definition = BuildDefinition.from_request_payload(data["definition"]) if "definition" in data else None
        return cls(str(data["id"]), str(data["buildNumber"]), data["status"], requested_by, build_repo, data.get("templateParameters", {}),
                   build_definition, from_ado_date_string(data.get("startTime")), from_ado_date_string(data.get("finishTime")),
                   from_ado_date_string(data.get("queueTime")), data["reason"], data["priority"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", build_id: str) -> "Build":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/builds/{build_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(
        cls, ado_client: "AdoClient", definition_id: str, source_branch: str = "refs/heads/main", permit_use_of_var_groups: bool = False,  # fmt: skip
    ) -> "Build":
        """`permit_var_groups` defines whether the variable group will be automatically allowed for the build or need manual approval."""
        # if permit_use_of_var_groups:
        #     rint(f"Variable Groups: {BuildDefinition.get_by_id(ado_client, definition_id).variable_groups}")
        #     for var_group_id in BuildDefinition.get_by_id(ado_client, definition_id).variable_groups:
        #         request = ado_client.session.patch(f"https://dev.azure.com/{ado_client.ado_org}/{definition_id}/_apis/pipelines/pipelinePermissions/variablegroup/{var_group_id}")  # fmt: skip
        #         rint(request.text, request.status_code)
        #         assert request.status_code <= 204
        return super()._create(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/builds?definitionId={definition_id}&api-version=7.1",
            {"reason": "An automated build created with the ado_wrapper Python library", "sourceBranch": source_branch},
        )  # type: ignore[return-value]

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", build_id: str) -> None:
        cls.delete_all_leases(ado_client, build_id)
        return super()._delete_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/builds/{build_id}?api-version=7.1",
            build_id,
        )

    def update(self, ado_client: "AdoClient", attribute_name: str, attribute_value: Any) -> None:
        return super()._update(
            ado_client, "patch",
            f"/{ado_client.ado_project}/_apis/build/builds/{self.build_id}?api-version=7.1",
            attribute_name, attribute_value, {attribute_name: attribute_value}  # fmt: skip
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> "list[Build]":
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/builds?api-version=7.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def create_and_wait_until_completion(cls, ado_client: "AdoClient", definition_id: str, branch_name: str = "main",
                                         max_timeout_seconds: int = 300) -> "Build":  # fmt: skip
        """Creates a build and waits until it is completed, or raises a TimeoutError if it takes too long.
        WARNING: This is a blocking operation, it will not return until the build is completed or the timeout is reached."""
        build = cls.create(ado_client, definition_id, branch_name, True)
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
    def delete_all_leases(ado_client: "AdoClient", build_id: str) -> None:
        leases_request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/builds/{build_id}/leases?api-version=7.1",
        )
        if leases_request.status_code != 200:
            if not ado_client.suppress_warnings:
                print(f"Could not delete leases, {leases_request.status_code}")
            return
        leases = leases_request.json()["value"]
        for lease in leases:
            lease_response = ado_client.session.delete(
                f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/retention/leases?ids={lease['leaseId']}&api-version=6.1",
            )
            assert lease_response.status_code <= 204

    @classmethod
    def get_all_by_definition(cls, ado_client: "AdoClient", definition_id: str) -> "list[Build]":
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/builds?definitions={definition_id}&api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def allow_on_environment(cls, ado_client: "AdoClient", definition_id: str, environment_id: str) -> PipelineAuthorisation:
        environment = Environment.get_by_id(ado_client, environment_id)
        return environment.add_pipeline_permission(ado_client, definition_id)

    @classmethod
    def get_latest(cls, ado_client: "AdoClient", definition_id: str) -> "Build | None":
        all_builds = cls.get_all_by_definition(ado_client, definition_id)
        builds_with_start = [x for x in all_builds if x.start_time is not None]
        return max(builds_with_start, key=lambda build: build.start_time) if builds_with_start else None  # type: ignore[return-value, arg-type]


# ========================================================================================================


@dataclass
class BuildDefinition(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions?view=azure-devops-rest-7.1"""

    build_definition_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True}, repr=False)
    path: str = field(repr=False)
    created_by: Member | None = field(repr=False)
    created_date: datetime | None = field(repr=False)
    build_repo: BuildRepository | None = field(repr=False)
    revision: str = field(default="1", repr=False)
    process: dict[str, str | int] | None = field(repr=False, default=None)  # Used internally, mostly ignore
    variables: dict[str, str] = field(default_factory=dict, repr=False)
    # variable_groups: list[int] = field(default_factory=list, repr=False)

    def __str__(self) -> str:
        return f"{self.name}, {self.build_definition_id}, created by {self.created_by}, created on {self.created_date!s}"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildDefinition":
        """Repo is not always present, Member is sometimes present, sometimes None"""
        created_by = Member.from_request_payload(data["authoredBy"]) if "authoredBy" in data else None  # fmt: skip
        build_repository = BuildRepository.from_request_payload(data["repository"]) if "repository" in data else None
        return cls(
            str(data["id"]), data["name"], data.get("description", ""), data.get("process", {"yamlFilename": "UNKNOWN"})["yamlFilename"],
            created_by, from_ado_date_string(data.get("createdDate")), build_repository, str(data["revision"]), data.get("process"),
            data.get("variables", {})  # fmt: skip
        )

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", build_definition_id: str) -> "BuildDefinition":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/definitions/{build_definition_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(
        cls, ado_client: "AdoClient", name: str, repo_id: str, repo_name: str, path_to_pipeline: str,
        description: str, agent_pool_id: str, branch_name: str = "main",  # fmt: skip
    ) -> "BuildDefinition":
        payload = get_build_definition(name, repo_id, repo_name, path_to_pipeline, description,
                                       ado_client.ado_project, agent_pool_id, branch_name)  # fmt: skip
        return super()._create(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/definitions?api-version=7.0",
            payload=payload,
        )  # type: ignore[return-value]

    def update(self, ado_client: "AdoClient", attribute_name: BuildDefinitionEditableAttribute, attribute_value: Any) -> None:
        if self.build_repo is None or self.process is None:
            raise ValueError("This build definition does not have a (repository or process) in its data, it cannot be updated")
        payload = (
            {"name": self.name, "id": self.build_definition_id, "revision": int(self.revision),
             "repository": {"id": self.build_repo.build_repository_id, "type": self.build_repo.type},
             "process": {"yamlFilename": self.process["yamlFilename"], "type": self.process["type"]}} | # fmt: skip
            {attribute_name: attribute_value}  # fmt: skip
        )
        super()._update(
            ado_client, "put",
            f"/{ado_client.ado_project}/_apis/build/definitions/{self.build_definition_id}?api-version=7.1", #secretsSourceDefinitionRevision={self.revision}&
            attribute_name, attribute_value, payload  # fmt: skip
        )
        self.revision = str(int(self.revision) + 1)

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", resource_id: str) -> None:
        for build in Build.get_all_by_definition(ado_client, resource_id):
            build.delete(ado_client)  # Can't remove from state because retention policies etc.
        return super()._delete_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/definitions/{resource_id}?forceDelete=true&api-version=7.1",
            resource_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> "list[BuildDefinition]":
        """WARNING: This returns a list of references, which don't have variable groups and more data included."""
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/build/definitions?api-version=7.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "BuildDefinition":
        return cls._get_by_abstract_filter(ado_client, lambda x: x.name == name)  # type: ignore[return-value, attr-defined]

    def get_all_builds_by_definition(self, ado_client: "AdoClient") -> "list[Build]":
        return Build.get_all_by_definition(ado_client, self.build_definition_id)

    def get_latest_build_by_definition(self, ado_client: "AdoClient") -> "Build | None":
        builds = self.get_all_builds_by_definition(ado_client)
        return max(builds, key=lambda build: build.start_time if build.start_time else datetime(2000, 1, 1)) if builds else None

    @classmethod
    def get_all_by_repo_id(cls, ado_client: "AdoClient", repo_id: str) -> "list[BuildDefinition]":
        return super()._get_all(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/build/definitions?repositoryId={repo_id}&repositoryType={'TfsGit'}&api-version=7.1",
        )  # type: ignore[return-value]


# ========================================================================================================

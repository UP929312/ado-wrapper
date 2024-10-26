from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal


from ado_wrapper.errors import ConfigurationError, UnknownError
from ado_wrapper.resources.repo import BuildRepository
from ado_wrapper.resources.users import Member
from ado_wrapper.resources.builds import Build
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string, build_hierarchy_payload

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

BuildDefinitionEditableAttribute = Literal["name", "description"]

# ========================================================================================================


def create_build_definition_payload(
    name: str, repo_id: str, path_to_pipeline: str, description: str, project: str,
    agent_pool_id: str | None = None, branch_name: str = "main"  # fmt: skip
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "repository": {
            "id": repo_id,
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
class BuildDefinition(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions?view=azure-devops-rest-7.1"""

    build_definition_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True})
    path: str = field(repr=False)
    created_by: Member | None = field(repr=False)
    created_date: datetime | None = field(repr=False)
    build_repo: BuildRepository | None = field(repr=False)
    revision: str = field(default="1", repr=False)
    process: dict[str, str | int] | None = field(repr=False, default=None)  # Used internally, mostly ignore
    variables: dict[str, str] = field(default_factory=dict, repr=False)
    # variable_groups: list[int] = field(default_factory=list, repr=False)

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
            f"/{ado_client.ado_project_name}/_apis/build/definitions/{build_definition_id}?api-version=7.1",
        )

    @classmethod
    def create(
        cls, ado_client: "AdoClient", name: str, repo_id: str, path_to_pipeline: str,
        description: str = "", agent_pool_id: str | None = None, branch_name: str = "main",  # fmt: skip
    ) -> "BuildDefinition":
        """Passing in no agent_pool_id will mean that the official Azure Agents will be used."""
        payload = create_build_definition_payload(
            name, repo_id, path_to_pipeline, description, ado_client.ado_project_name, agent_pool_id, branch_name,
        )  # fmt: skip
        return super()._create(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/definitions?api-version=7.0",
            payload=payload,
        )

    def update(self, ado_client: "AdoClient", attribute_name: BuildDefinitionEditableAttribute, attribute_value: Any) -> None:
        if self.build_repo is None or self.process is None:
            raise ValueError("This build definition does not have a (repository or process) in its data, it cannot be updated")
        payload = (
            {"name": self.name, "id": self.build_definition_id, "revision": int(self.revision),
             "repository": {"id": self.build_repo.build_repository_id, "type": self.build_repo.type},
             "process": {"yamlFilename": self.process["yamlFilename"], "type": self.process["type"]}}
            | {attribute_name: attribute_value}
        )  # fmt: skip
        super()._update(
            ado_client, "put",
            f"/{ado_client.ado_project_name}/_apis/build/definitions/{self.build_definition_id}?api-version=7.1",  # secretsSourceDefinitionRevision={self.revision}&
            attribute_name, attribute_value, payload  # fmt: skip
        )
        self.revision = str(int(self.revision) + 1)

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", resource_id: str) -> None:
        for build in Build.get_all_by_definition(ado_client, resource_id):
            build.delete(ado_client)  # Can't just remove from state because retention policies etc.
        # from ado_wrapper.resources.runs import Run  # Doesn't work, annoyingly
        # for run in Run.get_all_by_definition(ado_client, resource_id):
        #     ado_client.state_manager.remove_resource_from_state("Run", run.run_id)  # TODO: Not sure about this
        return super()._delete_by_id(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/definitions/{resource_id}?forceDelete=true&api-version=7.1",
            resource_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> "list[BuildDefinition]":
        """WARNING: This returns a list of references, which don't have variable groups and more data included."""
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/definitions?api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_build?definitionId={self.build_definition_id}"  # fmt: skip

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "BuildDefinition | None":
        return cls._get_by_abstract_filter(ado_client, lambda x: x.name == name)

    def get_all_builds_by_definition(self, ado_client: "AdoClient") -> "list[Build]":
        return Build.get_all_by_definition(ado_client, self.build_definition_id)

    def get_latest_build_by_definition(self, ado_client: "AdoClient") -> "Build | None":
        builds = self.get_all_builds_by_definition(ado_client)
        return max(builds, key=lambda build: build.start_time if build.start_time else datetime(2000, 1, 1)) if builds else None

    @classmethod
    def get_all_by_repo_id(cls, ado_client: "AdoClient", repo_id: str) -> "list[BuildDefinition]":
        return super()._get_all(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/build/definitions?repositoryId={repo_id}&repositoryType={'TfsGit'}&api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    @staticmethod
    def get_all_stages(
        ado_client: "AdoClient", definition_id: str,
        template_parameters: dict[str, Any] | None = None, branch_name: str = "main",
    ) -> list["BuildDefinitionStage"]:  # fmt: skip
        """Fetches a list of BuildDefinitionStage's, does not return the tasks results.
        Pass in custom template parameters as override key value pairs, or ignore this field to use the defaults."""
        # ================================================================================================================================
        # Fetch default template parameters, if the user doesn't pass them in, for the next stage.
        TEMPLATE_PAYLOAD = build_hierarchy_payload(
            ado_client, "build-web.pipeline-run-parameters-data-provider", route_id="build-web.pipeline-details-route", additional_properties={
                "pipelineId": int(definition_id),
                "sourceBranch": f"refs/heads/{branch_name}",
                "sourcePage": {"routeValues": {"viewname": "details"}},
            },  # fmt: skip
        )
        default_template_params_request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery/project/{ado_client.ado_project_name}?api-version=7.0-preview",
            json=TEMPLATE_PAYLOAD,
        ).json()
        error_message = (
            default_template_params_request.get("dataProviderExceptions", {}).get("ms.vss-build-web.pipeline-run-parameters-data-provider", {}).get("message", "")
        )  # fmt: skip
        if error_message == "Value cannot be null.\r\nParameter name: obj":
            raise UnknownError(
                "ERROR: There is a bug with ADO which means that build definitions created with the official API (and therefor through BuildDefinition.create())"
                + "will not work with stages_to_run as part for `Run.create()`, nor will they work with this function, `get_all_stages()`. "
                + "The current only way is to create the build definition through `BuildDefiniton.create_with_hierarchy()`."
                + "I spent a long time trying to fix this, and couldn't. Additionally, human made BuildDefinitions use the hierarchy method, so will also work."
            )
        if error_message.startswith("not found in repository"):
            raise ConfigurationError("Could not find the yaml file in the repo! Perhaps it's on a branch?")
        default_template_params_request_body = default_template_params_request["dataProviders"]["ms.vss-build-web.pipeline-run-parameters-data-provider"]["templateParameters"]  # fmt: skip
        default_template_parameters = {x["name"]: x["default"] for x in default_template_params_request_body}
        # ================================================================================================================================
        PAYLOAD = build_hierarchy_payload(
            ado_client, "build-web.pipeline-run-parameters-data-provider", route_id="build-web.pipeline-details-route", additional_properties={
                "pipelineId": definition_id,
                "sourceBranch": f"refs/heads/{branch_name}",
                "templateParameters": default_template_parameters,
            },  # fmt: skip
        )
        if template_parameters is not None:
            PAYLOAD["dataProviderContext"]["properties"]["templateParameters"] |= template_parameters
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery/project/{ado_client.ado_project_name}?api-version=7.0-preview",
            json=PAYLOAD,
        )
        if request.status_code != 200:
            raise UnknownError(f"Error! Could not fetch all stages! {request.status_code}, {request.text}")
        stages_list = request.json()["dataProviders"]["ms.vss-build-web.pipeline-run-parameters-data-provider"]["stages"]
        return [BuildDefinitionStage.from_request_payload(x) for x in stages_list]

    def allow_variable_group(self, ado_client: "AdoClient", variable_group_id: str) -> None:
        request = ado_client.session.patch(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/pipelines/pipelinePermissions/variablegroup/{variable_group_id}?api-version=6.0-preview.1",
            json={"pipelines": [{"id": self.build_definition_id, "authorized": True}]},
        )
        if request.status_code != 200:
            raise UnknownError(
                f"Could not permit variable group with id {variable_group_id} on this build definition!\n"
                + "- Sometimes, this is because it was run instantly after the build/run was created, try a time.sleep()?"
            )

    def allow_secure_file(self, ado_client: "AdoClient", secure_file_id: str) -> None:
        request = ado_client.session.patch(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/pipelines/pipelinePermissions/securefile/{secure_file_id}?api-version=6.0-preview.1",
            json={"pipelines": [{"id": self.build_definition_id, "authorized": True}]},
        )
        if request.status_code != 200:
            raise UnknownError(
                f"Could not permit secure_file with id {secure_file_id} on this build definition!\n"
                + "- Sometimes, this is because it was run instantly after the build/run was created, try a time.sleep()?"
            )

    @staticmethod
    def create_with_hierarchy(
        ado_client: "AdoClient", repo_id: str, repo_name: str, file_path: str, branch_name: str = "main", agent_pool_id: str | None = None
    ) -> "HierarchyCreatedBuildDefinition":
        return HierarchyCreatedBuildDefinition.create(ado_client, repo_id, repo_name, file_path, branch_name, agent_pool_id)


# ========================================================================================================


@dataclass
class HierarchyCreatedBuildDefinition(StateManagedResource):
    build_definition_id: str = field(metadata={"is_id_field": True})
    name: str

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "HierarchyCreatedBuildDefinition":
        return cls(str(data["id"]), data["name"])

    @classmethod
    def create(
        cls, ado_client: "AdoClient", repo_id: str, repo_name: str, file_path: str, branch_name: str = "main", agent_pool_id: str | None = None,  # fmt: skip
    ) -> "HierarchyCreatedBuildDefinition":
        PAYLOAD = build_hierarchy_payload(
            ado_client, "build-web.create-and-run-pipeline-data-provider", route_id="build-web.ci-definition-designer-route", additional_properties={
                "createOnly": True,  # createOnly=False means run it as well
                "sourceProvider": "tfsgit", "repositoryId": repo_id, "repositoryName": repo_name,
                "sourceBranch": branch_name, "filePath": file_path, "queue": agent_pool_id or "Azure Pipelines",
            },  # fmt: skip
        )
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery/project/{ado_client.ado_project_name}?api-version=6.1-preview",
            json=PAYLOAD,
        ).json()
        data = request["dataProviders"]["ms.vss-build-web.create-and-run-pipeline-data-provider"]["pipeline"]  # id, name, queueName
        instance = cls.from_request_payload(data)
        ado_client.state_manager.add_resource_to_state(cls.__name__, data["id"], instance.to_json())  # type: ignore[arg-type]
        return instance

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", build_definition_id: str) -> "HierarchyCreatedBuildDefinition":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/definitions/{build_definition_id}?api-version=7.1",
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", build_defintion_id: str) -> None:
        BuildDefinition.delete_by_id(ado_client, build_defintion_id)
        ado_client.state_manager.remove_resource_from_state(cls.__name__, build_defintion_id)  # type: ignore[arg-type]


@dataclass
class BuildDefinitionStage:
    stage_display_name: str
    stage_internal_name: str
    is_skippable: bool
    depends_on: list[str]

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildDefinitionStage":
        return cls(data["name"], data["refName"], data["isSkippable"], data["dependsOn"])

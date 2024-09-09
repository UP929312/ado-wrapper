from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal


from ado_wrapper.resources.repo import BuildRepository
from ado_wrapper.resources.users import Member
from ado_wrapper.resources.builds import Build
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string, requires_initialisation

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

BuildDefinitionEditableAttribute = Literal["name", "description"]

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
        cls, ado_client: "AdoClient", name: str, repo_id: str, repo_name: str, path_to_pipeline: str,
        description: str, agent_pool_id: str, branch_name: str = "main",  # fmt: skip
    ) -> "BuildDefinition":
        payload = get_build_definition(name, repo_id, repo_name, path_to_pipeline, description,
                                       ado_client.ado_project_name, agent_pool_id, branch_name)  # fmt: skip
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
            build.delete(ado_client)  # Can't remove from state because retention policies etc.
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
        requires_initialisation(ado_client)
        # ================================================================================================================================
        # Fetch default template parameters, if the user doesn't pass them in, for the next stage.
        TEMPLATE_PAYLOAD = {
            "contributionIds": ["ms.vss-build-web.pipeline-run-parameters-data-provider"], "dataProviderContext": {"properties": {
                    "pipelineId": int(definition_id), "sourceBranch": f"refs/heads/{branch_name}",
                    "sourcePage": {"routeId": "ms.vss-build-web.pipeline-details-route", "routeValues": {"project": ado_client.ado_project_name}}
                }
            },
        }  # fmt: skip
        default_template_parameters_request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery/project/{ado_client.ado_project_id}?api-version=7.0-preview",
            json=TEMPLATE_PAYLOAD,
        ).json()["dataProviders"]["ms.vss-build-web.pipeline-run-parameters-data-provider"]["templateParameters"]
        default_template_parameters = {x["name"]: x["default"] for x in default_template_parameters_request}
        # ================================================================================================================================
        PAYLOAD = {
            "contributionIds": ["ms.vss-build-web.pipeline-run-parameters-data-provider"], "dataProviderContext": {"properties": {
                "pipelineId": definition_id, "sourceBranch": f"refs/heads/{branch_name}", "templateParameters": default_template_parameters,
                "sourcePage": {"routeId": "ms.vss-build-web.pipeline-details-route", "routeValues": {"project": ado_client.ado_project_name}},
            }},
        }  # fmt: skip
        if template_parameters is not None:
            PAYLOAD["dataProviderContext"]["properties"]["templateParameters"] |= template_parameters  # type: ignore[index]
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery/project/{ado_client.ado_project_id}?api-version=7.0-preview",
            json=PAYLOAD,
        )
        assert request.status_code == 200
        stages_list = request.json()["dataProviders"]["ms.vss-build-web.pipeline-run-parameters-data-provider"]["stages"]
        return [BuildDefinitionStage.from_request_payload(x) for x in stages_list]


# ========================================================================================================


@dataclass
class BuildDefinitionStage:
    stage_display_name: str
    stage_internal_name: str
    is_skippable: bool
    depends_on: list[str]

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildDefinitionStage":
        return cls(
            data["name"],
            data["refName"],
            data["isSkippable"],
            data["dependsOn"],
        )

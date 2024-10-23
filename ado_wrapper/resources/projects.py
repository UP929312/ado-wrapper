from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import DeletionFailed, NoElevatedPrivilegesError
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.project_settings import (
    ProjectPipelineSettings, ProjectBuildQueueSettings, ProjectRetentionPolicySettings, ProjectRepositorySettings,
    ProjectRepositoryPolicySettings, ProjectOverviewSettings, ProjectTestRetentionSettings, ProjectArtifactStorageSettings,
)  # fmt: skip

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

ProjectVisibilityType = Literal["private", "public"]
TemplateTypes = Literal["Agile", "Scrum", "CMMI", "Basic"]
template_types_mapping: dict[TemplateTypes, str] = {
    "Basic": "b8a3a935-7e91-48b8-a94c-606d37c3e9f2",  # (same as CMMI, but used for a simpler version)
    "Agile": "6b724908-ef14-45cf-84f8-768b5384da45",
    "Scrum": "adcc42ab-9882-485e-a3ed-7678f01f66bc",
    "CMMI": "27450541-8e31-4150-9947-dc59f998fc01",  # (Capability Maturity Model Integration)
}
ProjectStatus = Literal["all", "createPending", "deleted", "deleting", "new", "unchanged", "wellFormed", "notSet"]  # notSet is sketchy?


@dataclass
class Project(StateManagedResource):
    "https://learn.microsoft.com/en-us/rest/api/azure/devops/core/projects?view=azure-devops-rest-7.1"
    project_id: str = field(metadata={"is_id_field": True})  # None are editable
    name: str
    description: str
    visibility: ProjectVisibilityType | None
    creation_status: ProjectStatus
    last_update_time: datetime | None = None

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Project":
        return cls(data["id"], data.get("name", "CREATING"), data.get("description", ""),
                   data.get("visibility"), data.get("state", "notSet"), data.get("lastUpdateTime"))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", project_id: str) -> "Project":
        return super()._get_by_url(
            ado_client,
            f"/_apis/projects/{project_id}?api-version=7.1",
        )

    @classmethod
    def create(cls, ado_client: "AdoClient", name: str, project_description: str, template_type: TemplateTypes) -> "Project":
        if not ado_client.has_elevate_privileges:
            raise NoElevatedPrivilegesError(
                "To create a project, you must raise your privileges using the `with ado_client.elevated_privileges()` context manager!"
            )
        return super()._create(
            ado_client,
            "/_apis/projects?api-version=7.1",
            payload={
                "name": name, "description": project_description, "visibility": "private",
                "capabilities": {
                    "versioncontrol": {"sourceControlType": "Git"},
                    "processTemplate": {"templateTypeId": template_types_mapping[template_type]},
                },
            },  # fmt: skip
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", project_id: str) -> None:
        if not ado_client.has_elevate_privileges:
            raise NoElevatedPrivilegesError(
                "To delete a project, you must raise your privileges using the `with ado_client.elevated_privileges()` context manager!"
            )
        try:
            return super()._delete_by_id(
                ado_client,
                f"/_apis/projects/{project_id}?api-version=7.1",
                project_id,
            )
        except DeletionFailed:
            ado_client.state_manager.remove_resource_from_state(cls.__name__, project_id)  # type: ignore[arg-type]
            # Deletion fails sometimes, although it still deletes just fine?
            # raise DeletionFailed("Error, could not delete, perhaps it wasn't finished creating yet, or already deleted?")

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["Project"]:
        return super()._get_all(
            ado_client,
            "/_apis/projects?api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", project_name: str) -> "Project | None":
        return cls._get_by_abstract_filter(ado_client, lambda project: project.name == project_name)

    # ======================== Project settings ========================== #
    get_pipeline_settings = ProjectPipelineSettings.get_pipeline_settings
    get_build_queue_settings = ProjectBuildQueueSettings.get_build_queue_settings
    get_retention_policy_settings = ProjectRetentionPolicySettings.get_retention_policy_settings
    get_repository_settings = ProjectRepositorySettings.get_repository_settings
    get_repository_policy_settings = ProjectRepositoryPolicySettings.get_repository_policy_settings
    get_overview_settings = ProjectOverviewSettings.get_project_overview_settings
    get_test_retention_settings = ProjectTestRetentionSettings.get_test_retention_settings
    set_test_retention_settings = ProjectTestRetentionSettings.set_test_retention_settings
    get_artifact_storage_settings = ProjectArtifactStorageSettings.get_artifact_storage_settings

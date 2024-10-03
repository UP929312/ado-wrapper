import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import DeletionFailed, NoElevatedPrivilegesError, UnknownError
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import build_hierarchy_payload

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

ProjectVisibilityType = Literal["private", "public"]
TemplateTypes = Literal["Agile", "Scrum", "CMMI", "Basic"]
template_types_mapping: dict[TemplateTypes, str] = {
    "Agile": "6b724908-ef14-45cf-84f8-768b5384da45",
    "Scrum": "adcc42ab-9882-485e-a3ed-7678f01f66bc",
    "CMMI": "27450541-8e31-4150-9947-dc59f998fc01",  # (Capability Maturity Model Integration)
    "Basic": "27450541-8e31-4150-9947-dc59f998fc01",  # (same as CMMI, but used for a simpler version)
}
ProjectStatus = Literal["all", "createPending", "deleted", "deleting", "new", "unchanged", "wellFormed", "notSet"]  # notSet is sketchy?
# ====
ProjectRepositorySettingType = Literal["default_branch_name", "disable_tfvc_repositories",
                                       "new_repos_created_branches_manage_permissions_enabled", "pull_request_as_draft_by_default"]  # fmt: skip
project_repository_settings_mapping = {
    "DefaultBranchName": "default_branch_name",
    "DisableTfvcRepositories": "disable_tfvc_repositories",
    "NewReposCreatedBranchesManagePermissionsEnabled": "new_repos_created_branches_manage_permissions_enabled",
    "PullRequestAsDraftByDefault": "pull_request_as_draft_by_default",
}
project_repository_settings_mapping_reversed = {value: key for key, value in project_repository_settings_mapping.items()}


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
    def create(cls, ado_client: "AdoClient", project_name: str, project_description: str, template_type: TemplateTypes) -> "Project":
        if not ado_client.has_elevate_privileges:
            raise NoElevatedPrivilegesError(
                "To create a project, you must raise your privileges using with the ado_client.elevated_privileges() context manager!"
            )
        return super()._create(
            ado_client,
            "/_apis/projects?api-version=7.1",
            payload={
                "name": project_name, "description": project_description, "visibility": "private",
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
                "To delete a project, you must raise your privileges using with the ado_client.elevated_privileges() context manager!"
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

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", project_name: str) -> "Project | None":
        return cls._get_by_abstract_filter(ado_client, lambda project: project.name == project_name)

    @staticmethod
    def get_pipeline_settings(ado_client: "AdoClient", project_name: str | None = None) -> dict[str, bool]:
        PAYLOAD = build_hierarchy_payload(
            ado_client, "build-web.pipelines-general-settings-data-provider", route_id="admin-web.project-admin-hub-route"
        )
        PAYLOAD["dataProviderContext"]["properties"]["sourcePage"]["routeValues"]["project"] = project_name or ado_client.ado_project_name
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.0-preview",
            json=PAYLOAD,
        ).json()
        mapping = request["dataProviders"]["ms.vss-build-web.pipelines-general-settings-data-provider"]
        return {key: value["enabled"] for key, value in mapping.items() if isinstance(value, dict)}

    @staticmethod
    def get_build_queue_settings(ado_client: "AdoClient") -> dict[str, Any]:
        """A method which returns the amount of free and paid for parallel jobs within AzureDevops.
        To get the settings for another project, use ado_client.assume_project()."""
        # Can't use build_hierarchy_payload because it's wrapped in context...
        PAYLOAD = {"contributionIds": ["ms.vss-build-web.build-queue-hub-data-provider"], "context": {"properties": {
                   "sourcePage": {"routeId": "ms.vss-admin-web.project-admin-hub-route"}}}}  # fmt: skip
        # ============================================================================================================
        private_projects_request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/dataProviders/query?api-version=7.0-preview.1",
            json=PAYLOAD,
        ).json()["data"]["ms.vss-build-web.build-queue-hub-data-provider"]["taskHubLicenseDetails"]
        # ============================================================================================================
        PAYLOAD["context"]["properties"]["FetchPublicResourceUsage"] = True  # type: ignore[index]
        public_projects_request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/dataProviders/query?api-version=7.0-preview.1",
            json=PAYLOAD,
        ).json()["data"]["ms.vss-build-web.build-queue-hub-data-provider"]["resourceUsages"]
        public_microsoft_hosted = [x["resourceLimit"] for x in public_projects_request if x["resourceLimit"]["isHosted"]][0]
        public_self_hosted = [x["resourceLimit"] for x in public_projects_request if not x["resourceLimit"]["isHosted"]][0]
        # ============================================================================================================
        data = {
            "private_projects": {
                "microsoft_hosted": {
                    "monthly_purchases": private_projects_request["purchasedHostedLicenseCount"],
                },
                "self_hosted": {
                    "free_parallel_jobs": private_projects_request["freeLicenseCount"],
                    "visual_studio_enterprise_subscribers": private_projects_request["enterpriseUsersCount"],
                    "monthly_purchases": private_projects_request["purchasedLicenseCount"],
                },
            },
            "public_projects": {
                "microsoft_hosted": {
                    "free_parallel_jobs": int(public_microsoft_hosted["resourceLimitsData"]["FreeCount"]),
                    "monthly_purchases": int(public_microsoft_hosted["resourceLimitsData"]["PurchasedCount"]),
                },
                "self_hosted": {
                    "free_parallel_jobs": (
                        public_self_hosted["resourceLimitsData"]["FreeCount"]
                        if int(public_self_hosted["resourceLimitsData"]["FreeCount"]) < 10000
                        else "Unlimited"
                    )
                },
            },
        }
        return data

    @staticmethod
    def get_retention_policy_settings(ado_client: "AdoClient") -> dict[str, Any]:
        """Gets a project's Retention policy settings, including how many days to keep releases, to delete the builds, etc."""
        request = ado_client.session.get(
            f"https://vsrm.dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/Release/releasesettings?api-version=7.0-preview.1",
        ).json()["retentionSettings"]
        return {
            "maximum_retention_policy": {
                "days_to_retain_a_release": request["maximumEnvironmentRetentionPolicy"]["daysToKeep"],
                "minimum_releases_to_keep": request["maximumEnvironmentRetentionPolicy"]["releasesToKeep"],
            },
            "default_retention_policy": {
                "days_to_retain_a_release": request["defaultEnvironmentRetentionPolicy"]["daysToKeep"],
                "minimum_releases_to_keep": request["defaultEnvironmentRetentionPolicy"]["releasesToKeep"],
                "retain_build": request["defaultEnvironmentRetentionPolicy"]["retainBuild"],
            },
            "permanently_destory_releases": {
                "days_to_keep_releases_after_deletion": request["daysToKeepDeletedReleases"],
            },
        }

    @staticmethod
    def get_repository_settings(
        ado_client: "AdoClient", project_name: str | None = None
    ) -> dict[ProjectRepositorySettingType, "ProjectRepositorySettings"]:  # fmt: skip
        return ProjectRepositorySettings.get_by_project(ado_client, project_name)


@dataclass
class ProjectRepositorySettings:
    programmatic_name: ProjectRepositorySettingType
    internal_name: str = field(repr=False)  # Internal key, e.g. DefaultBranchName
    title: str
    description: str = field(repr=False)
    setting_enabled: bool  # If this setting is taking effect
    disabled_by_inheritence: bool  # If this setting cannot be enabled because of inherited settings
    override_string_value: str | None  # For default_branch_name, an override string value
    default_value: str | None = field(repr=False)  # For default_branch_name, equal to "main"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ProjectRepositorySettings":
        return cls(project_repository_settings_mapping[data["key"]], data["key"], data["title"], data["displayHtml"],  # type: ignore[arg-type]
                   data["value"], data.get("isDisabled", False), data["textValue"], data["defaultTextValue"])  # fmt: skip

    @staticmethod
    def _get_request_verification_code(ado_client: "AdoClient", project_name: str | None = None) -> str:
        request_verification_token_body = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{project_name or ado_client.ado_project_name}/_settings/repositories?_a=settings",
        ).text
        LINE_PREFIX = '<input type="hidden" name="__RequestVerificationToken" value="'
        line = [x for x in request_verification_token_body.split("\n") if LINE_PREFIX in x][0]
        request_verification_token = line.strip(" ").removeprefix(LINE_PREFIX).split('"')[0]
        return request_verification_token

    @classmethod
    def get_by_project(
        cls, ado_client: "AdoClient", project_name: str | None = None
    ) -> dict[ProjectRepositorySettingType, "ProjectRepositorySettings"]:  # fmt: skip
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{project_name or ado_client.ado_project_name}/_api/_versioncontrol/AllGitRepositoriesOptions?__v=5"
        ).json()
        list_of_settings = [cls.from_request_payload(x) for x in request["__wrappedArray"]]
        return {setting.programmatic_name: setting for setting in list_of_settings}

    @classmethod
    def update_default_branch_name(
        cls, ado_client: "AdoClient", new_default_branch_name: str, project_name: str | None = None,  # fmt: skip
    ) -> None:
        request_verification_token = cls._get_request_verification_code(ado_client, project_name)
        body = {
            "repositoryId": "00000000-0000-0000-0000-000000000000",
            "option": json.dumps({"key": "DefaultBranchName", "value": True, "textValue": new_default_branch_name}),
            "__RequestVerificationToken": request_verification_token,
        }
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{project_name or ado_client.ado_project_name}/_api/_versioncontrol/UpdateRepositoryOption?__v=5&repositoryId=00000000-0000-0000-0000-000000000000",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if request.status_code != 200:
            raise UnknownError(f"Error, updating the default branch name failed! {request.status_code}, {request.text}")

    @classmethod
    def set_project_repository_setting(cls, ado_client: "AdoClient", repository_setting: ProjectRepositorySettingType,
                                       state: bool, project_name: str | None = None, ) -> None:  # fmt: skip
        request_verification_token = cls._get_request_verification_code(ado_client, project_name)
        body = {
            "repositoryId": "00000000-0000-0000-0000-000000000000",
            "option": json.dumps({"key": project_repository_settings_mapping_reversed[repository_setting], "value": state, "textValue": None}),  # fmt: skip
            "__RequestVerificationToken": request_verification_token,
        }
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{project_name or ado_client.ado_project_name}/_api/_versioncontrol/UpdateRepositoryOption?__v=5&repositoryId=00000000-0000-0000-0000-000000000000",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if request.status_code != 200:
            raise UnknownError(f"Error, updating that repo setting failed! {request.status_code}, {request.text}")

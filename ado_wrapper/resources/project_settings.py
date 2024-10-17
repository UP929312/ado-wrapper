import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import UnknownError
from ado_wrapper.utils import build_hierarchy_payload, requires_initialisation

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

# ====
# Repository Settings
ProjectRepositorySettingType = Literal["default_branch_name", "disable_tfvc_repositories",
                                       "new_repos_created_branches_manage_permissions_enabled", "pull_request_as_draft_by_default"]  # fmt: skip
ProjectRepositorySettingDisplayType = Literal["DefaultBranchName", "DisableTfvcRepositories", "NewReposCreatedBranchesManagePermissionsEnabled",
                                              "PullRequestAsDraftByDefault"]  # fmt: skip
project_repository_settings_mapping = {
    "DefaultBranchName": "default_branch_name",
    "DisableTfvcRepositories": "disable_tfvc_repositories",
    "NewReposCreatedBranchesManagePermissionsEnabled": "new_repos_created_branches_manage_permissions_enabled",
    "PullRequestAsDraftByDefault": "pull_request_as_draft_by_default",
}
project_repository_settings_mapping_reversed = {value: key for key, value in project_repository_settings_mapping.items()}
# ====
# Repository Policies
RepoPolicyProgrammaticName = Literal["commit_author_email_validation", "file_path_validation", "enforce_consistant_case",
                                     "reserved_names_restriction", "maximum_path_length", "maximum_file_size"]  # fmt: skip
RepoPolicyDisplayTypes = Literal["Commit author email validation", "File name restriction", "Git repository settings",
                                 "Reserved names restriction", "Path Length restriction", "File size restriction"]  # fmt: skip
display_to_internal_names: dict[RepoPolicyDisplayTypes, RepoPolicyProgrammaticName] = {
    "Commit author email validation": "commit_author_email_validation",
    "File name restriction": "file_path_validation",
    "Git repository settings": "enforce_consistant_case",
    "Reserved names restriction": "reserved_names_restriction",
    "Path Length restriction": "maximum_path_length",
    "File size restriction": "maximum_file_size",
}
policy_to_structure_path = {
    "commit_author_email_validation": "authorEmailPatterns",
    "file_path_validation": "filenamePatterns",
    "enforce_consistant_case": "enforceConsistentCase",
    "maximum_path_length": "maxPathLength",
    "maximum_file_size": "maximumGitBlobSizeInBytes",
}
# ====
# Overview settings
ProjectServicesType = Literal["Artifacts", "Test Plans", "Pipelines", "Repos", "Boards"]
services_mapping: dict[str, ProjectServicesType] = {
    "ms.azure-artifacts.feature": "Artifacts",
    "ms.vss-test-web.test": "Test Plans",
    "ms.vss-build.pipelines": "Pipelines",
    "ms.vss-code.version-control": "Repos",
    "ms.vss-work.agile": "Boards",
}
# ===
# Arifact storage settings
artifact_storage_types_mapping = {
    "package_storage": "logicalPackageStorageSizeInBytes",
    "symbols": "logicalSymbolsUsageInBytes",
    "pipeline_artifact": "logicalSymbolsUsageInBytes",
    "pipeline_caching": "logicalPipelineCacheStorageSizeInBytes",
    "drop_storage": "logicalDropStorageSizeInBytes",
}
# ===


class ProjectBuildQueueSettings:
    @staticmethod
    def get_build_queue_settings(ado_client: "AdoClient") -> dict[str, Any]:
        """A method which returns the amount of free and paid for parallel jobs within AzureDevops.\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/buildqueue?_a=concurrentJobs"""
        # Can't use build_hierarchy_payload because it's wrapped in `context`...
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
        # ============================================================================================================
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


class ProjectPipelineSettings:
    @staticmethod
    def get_pipeline_settings(ado_client: "AdoClient", project_name: str | None = None) -> dict[str, bool]:
        """Returns the values from https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/settings"""
        PAYLOAD = build_hierarchy_payload(
            ado_client, "build-web.pipelines-general-settings-data-provider", route_id="admin-web.project-admin-hub-route"
        )
        PAYLOAD["dataProviderContext"]["properties"]["sourcePage"]["routeValues"]["project"] = project_name or ado_client.ado_project_name
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.0-preview",
            json=PAYLOAD,
        ).json()
        # TODO: Add Retention policies from
        # https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/settings
        # At the top
        mapping: dict[str, Any] = request["dataProviders"]["ms.vss-build-web.pipelines-general-settings-data-provider"]
        return {key: value["enabled"] for key, value in mapping.items() if isinstance(value, dict)}


class ProjectRetentionPolicySettings:
    @staticmethod
    def get_retention_policy_settings(ado_client: "AdoClient") -> dict[str, Any]:
        """Gets a project's Retention policy settings, including how many days to keep releases, to delete the builds, etc. \n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/release"""
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


@dataclass
class ProjectRepositorySettings:
    programmatic_name: ProjectRepositorySettingType
    internal_name: ProjectRepositorySettingDisplayType = field(repr=False)  # Internal key, e.g. DefaultBranchName
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
    def get_repository_settings(
        cls, ado_client: "AdoClient", project_name: str | None = None
    ) -> dict[ProjectRepositorySettingType, "ProjectRepositorySettings"]:  # fmt: skip
        """Get all the settings from:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/repositories?_a=settings"""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{project_name or ado_client.ado_project_name}/_api/_versioncontrol/AllGitRepositoriesOptions?__v=5"
        ).json()
        list_of_settings = [cls.from_request_payload(x) for x in request["__wrappedArray"]]
        return {setting.programmatic_name: setting for setting in list_of_settings}

    @classmethod
    def update_default_branch_name(
        cls, ado_client: "AdoClient", new_default_branch_name: str, project_name: str | None = None,  # fmt: skip
    ) -> None:
        """Update the default branch name for newly created repos, found:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/repositories?_a=settings"""
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
    def set_project_repository_setting(
        cls, ado_client: "AdoClient", repository_setting: ProjectRepositorySettingType, state: bool, project_name: str | None = None
    ) -> None:  # fmt: skip
        """Set all the settings from:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/repositories?_a=settings"""
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


@dataclass
class ProjectRepositoryPolicySettings:
    policy_id: str
    programmatic_name: RepoPolicyProgrammaticName
    display_name: RepoPolicyDisplayTypes
    enabled: bool
    value: list[str] | int | None  # e.g the number, 10240 bytes (10MB) or the allowed email rule, e.g. ["@gmail.com",]

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ProjectRepositoryPolicySettings":
        display_name = data["type"]["displayName"]
        programmatic_name = display_to_internal_names[display_name]
        value = (data.get("settings", {}).get(policy_to_structure_path[programmatic_name])
                 if programmatic_name != "reserved_names_restriction" else None)  # fmt: skip
        return cls(data["id"], programmatic_name, display_name, enabled=data["isEnabled"], value=value)

    @classmethod
    def get_repository_policy_settings(cls, ado_client: "AdoClient") -> list["ProjectRepositoryPolicySettings"]:
        """Returns all the settings from:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/repositories?_a=policies \n
        For only enabled policies. Those which are missing are not enabled."""
        PAYLOAD = build_hierarchy_payload(
            ado_client, "code-web.repository-policies-data-provider", "admin-web.project-admin-hub-route", additional_properties={
                "projectId": ado_client.ado_project_id,
            }  # fmt: skip
        )
        request: dict[str, dict[str, list[Any]]] = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=5.0-preview.1",
            json=PAYLOAD,
        ).json()["dataProviders"]["ms.vss-code-web.repository-policies-data-provider"]["policyGroups"]  # fmt: skip
        policies_data = [x["currentScopePolicies"][0] for x in request.values()]
        policies = [cls.from_request_payload(x) for x in policies_data if x["type"]["displayName"] in display_to_internal_names]
        return policies


class ProjectOverviewSettings:
    @staticmethod
    def get_project_overview_settings(ado_client: "AdoClient") -> dict[str, Any]:
        """Gets the results from this page:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/projectOverview"""
        # Cannot replace ado_client.ado_project_id with ado_project name because it returns the wrong results...
        requires_initialisation(ado_client)
        # =====
        PAYLOAD = {"featureIds": list(services_mapping.keys())}
        request: dict[str, dict[str, str]] = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/FeatureManagement/FeatureStatesQuery/host/project/{ado_client.ado_project_id}?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()["featureStates"]
        features: dict[ProjectServicesType, bool] = {services_mapping[key]: value["state"] == "enabled" for key, value in request.items()}  # fmt: skip
        # =====
        project_usage_limits: dict[str, dict[str, int]] = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_id}/_apis/ResourceUsage?api-version=7.1-preview.1",
        ).json()["value"]
        # =====
        return {"features": features, "project_usage_limits": project_usage_limits}


class ProjectTestRetentionSettings:
    @staticmethod
    def get_test_retention_settings(ado_client: "AdoClient") -> dict[str, int]:
        """Gets the results from this page, including how long to keep automated and manual test runs & results:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/testmanagement"""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/test/ResultRetentionSettings?api-version=7.0-preview.1",
        ).json()
        return {
            "automated_result_retention_in_days": request["automatedResultsRetentionDuration"],
            "manual_result_retention_in_days": request["manualResultsRetentionDuration"],
        }

    @staticmethod
    def set_test_retention_settings(ado_client: "AdoClient", automated_result_retention_in_days: int, manual_result_retention_in_days: int) -> None:  # fmt: skip
        """Sets the results from this page, including how long to keep automated and manual test runs & results:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/testmanagement \n"""
        PAYLOAD = {
            "automatedResultsRetentionDuration": automated_result_retention_in_days,
            "manualResultsRetentionDuration": manual_result_retention_in_days,
            "lastUpdatedBy": None,
            "lastUpdatedDate": None,
        }
        request = ado_client.session.patch(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/test/ResultRetentionSettings?api-version=7.1-preview.1",
            json=PAYLOAD,
        )
        if request.status_code != 200:
            raise UnknownError(f"Unknown error when setting test retention settings: {request.text}")


class ProjectArtifactStorageSettings:
    @staticmethod
    def get_artifact_storage_settings(ado_client: "AdoClient") -> dict[str, int | None]:
        """Gets the results from this page:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/storage \n
        All results are returned as a number of bytes."""
        PAYLOAD = build_hierarchy_payload(
            ado_client, "storage-web.artifacts-usage-breakdown-data-provider", "admin-web.project-admin-hub-route"
        )
        request: dict[str, Any] = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()["dataProviders"]["ms.vss-storage-web.artifacts-usage-breakdown-data-provider"]
        data = {
            key: [x for x in request["feedsUsage"] if value in x][0][value]
            if [x for x in request["feedsUsage"] if value in x] else None
            for key, value in artifact_storage_types_mapping.items()
        }  # fmt: skip
        return data

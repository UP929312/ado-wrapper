import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import UnknownError
from ado_wrapper.utils import build_hierarchy_payload

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

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
# ====
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


@dataclass
class ProjectRepositoryPolicies:
    policy_id: str
    programmatic_name: RepoPolicyProgrammaticName
    display_name: RepoPolicyDisplayTypes
    enabled: bool
    value: list[str] | int | None  # e.g the number, 10240 bytes (10MB) or the allowed email rule, e.g. ["@gmail.com",]

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ProjectRepositoryPolicies":
        display_name = data["type"]["displayName"]
        programmatic_name = display_to_internal_names[display_name]
        value = (data.get("settings", {}).get(policy_to_structure_path[programmatic_name])
                 if programmatic_name != "reserved_names_restriction" else None)  # fmt: skip
        return cls(data["id"], programmatic_name, display_name, enabled=data["isEnabled"], value=value)

    @classmethod
    def get_by_project(cls, ado_client: "AdoClient") -> list["ProjectRepositoryPolicies"]:
        """Returns all the settings from:\n
        https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/repositories?_a=policies \n
        For only enabled policies. Those which are missing are not enabled."""
        PAYLOAD = build_hierarchy_payload(
            ado_client, "code-web.repository-policies-data-provider", "admin-web.project-admin-hub-route", additional_properties={
                "projectId": ado_client.ado_project_id,
            }  # fmt: skip
        )
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=5.0-preview.1",
            json=PAYLOAD,
        ).json()["dataProviders"]["ms.vss-code-web.repository-policies-data-provider"]["policyGroups"]  # fmt: skip
        policies_data = [x["currentScopePolicies"][0] for x in request.values()]
        policies = [cls.from_request_payload(x) for x in policies_data if x["type"]["displayName"] in display_to_internal_names]
        return policies


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

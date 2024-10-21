import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Any

from ado_wrapper.utils import build_hierarchy_payload

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

# ========================================================================
# OrganisationPolicySettings
groups_mapping = {
    "application_connection_policies": "applicationConnection",
    "security_policies": "security",
    "user_policies": "user",
}
mapping = {
    "application_connection_policies": {
        "third_party_application_access_via_oauth": "Policy.DisallowOAuthAuthentication",
        "ssh_authentication": "Policy.DisallowSecureShell",
    },
    "security_policies": {
        "log_audit_events": "Policy.LogAuditEvents",
        "allow_public_projects": "Policy.AllowAnonymousAccess",
        "additional_protections_when_using_public_package_registries": "Policy.ArtifactsExternalPackageProtectionToken",
        "enable_ip_conditional_access_policy_validation": "Policy.EnforceAADConditionalAccess",
    },
    "user_policies": {
        "external_guest_access": "Policy.DisallowAadGuestUserAccess",
        "allow_team_and_project_administrators_to_invite_new_users": "Policy.AllowTeamAdminsInvitationsAccessToken",
        "request_access": "Policy.AllowRequestAccessToken",
    },
}
inverted_organisation_policy_settings = ["third_party_application_access_via_oauth", "ssh_authentication", "external_guest_access"]
# ========================================================================
# OrganisationRepositorySettings
OrgRepoSettingsProgrammaticNamesTypes = Literal[
    "gravatar_images", "default_branch_name_for_new_repositories", "disable_creation_of_tfvc_repositories"
]  # fmt: skip
OrgRepoSettingsInternalNamesTypes = Literal[
    "GravatarEnabled", "DefaultBranchName", "DisableTfvcRepositories"
]  # fmt: skip
org_repo_settings_mapping: dict[OrgRepoSettingsInternalNamesTypes, OrgRepoSettingsProgrammaticNamesTypes] = {
    "GravatarEnabled": "gravatar_images",
    "DefaultBranchName": "default_branch_name_for_new_repositories",
    "DisableTfvcRepositories": "disable_creation_of_tfvc_repositories",
}
# ========================================================================
# OrganisationPipelineSettings
org_pipeline_settings_mapping = {
    # TODO: Replace these with programmatic_names_instead?
    "statusBadgesArePrivate": "Disable anonymous access to badges",
    "enforceSettableVar": "Limit variables that can be set at queue time",
    "enforceJobAuthScope": "Limit job authorization scope to current project for release pipelines",
    "enforceJobAuthScopeForReleases": "Limit job authorization scope to current project for non-release pipelines",
    "enforceReferencedRepoScopedToken": "Protect access to repositories in YAML pipelines",
    "disableStageChooser": "Disable stage chooser",
    "disableClassicBuildPipelineCreation": "Disable creation of classic release pipelines",
    "disableClassicReleasePipelineCreation": "Disable creation of classic build pipelines",
    #
    "forkProtectionEnabled": "Limit building pull requests from forked GitHub repositories",
    "disableImpliedYAMLCiTrigger": "Disable implied YAML CI trigger",
    #
    "disableInBoxTasksVar": "Disable built-in tasks",
    "disableMarketplaceTasksVar": "Disable Marketplace tasks",
    "disableNode6TasksVar": "Disable Node 6 tasks",
    "enableShellTasksArgsSanitizing": "Enable shell tasks arguments validation",
    # "isTaskLockdownFeatureEnabled": "",
    # "disableClassicPipelineCreation": "",
    # "auditEnforceSettableVar": "",
    # "enableShellTasksArgsSanitizingAudit": "",
    # "hasManagePipelinePoliciesPermission": "",
    # "buildsEnabledForForks": "",
    # "enforceJobAuthScopeForForks": "",
    # "enforceNoAccessToSecretsFromForks": "",
    # "isCommentRequiredForPullRequest": "",
    # "requireCommentsForNonTeamMembersOnly": "",
    # "requireCommentsForNonTeamMemberAndNonContributors": "",
}
# ========================================================================


class OrganisatioOverviewSettings:
    @staticmethod
    def get_overview_settings(ado_client: "AdoClient") -> dict[str, dict[str, int]]:
        """Returns the `Organization Usage Limit` from https://dev.azure.com/{ado_client.ado_org_name}/_settings/organizationOverview"""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/ResourceUsage?api-version=7.1-preview.1",
        ).json()["value"]
        return request  # type: ignore[no-any-return]


# class OrganisationBillingSettings:
#     @staticmethod
#     def get_billing_settings(ado_client: "AdoClient") -> dict[str, dict[str, int]]:
#         bearer_token = ""
#         request = ado_client.session.get(
#             f"https://azdevopscommerce.dev.azure.com/938ee696-1bef-4188-85a3-9c25ebc84c21/_apis/AzComm/MeterResource",
#             # f"https://azdevopscommerce.dev.azure.com/{ado_client.ado_org_name}/_apis/AzComm/MeterResource?api-version=7.1-preview.1",
#             headers={
#                 "accept": "application/json;api-version=5.1-preview.1;excludeUrls=true;enumsAsNumbers=true;msDateFormat=true;noArrayWrap=true",
#                 "authorization": f"Bearer {bearer_token}",
#             }
#         )
#         print(request.text)
#         return request.status_code  # type: ignore


class OrganisationSecurityPolicySettings:
    @staticmethod
    def get_organisation_security_policy_settings(ado_client: "AdoClient") -> dict[str, dict[str, bool]]:
        """Returns a mapping of category to policy->status (True or False) from
        https://dev.azure.com/{ado_client.ado_org_name/_settings/organizationPolicy"""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_settings/organizationPolicy?api-version=7.1-preview.1",
        )
        string_json = request.text.split('<script id="dataProviders" type="application/json">')[1].split("</script>")[0]
        data = json.loads(string_json)
        policies = data["data"]["ms.vss-admin-web.organization-policies-data-provider"]["policies"]
        returned_mapping = {
            programmatic_group: {
                key: [x["policy"]["value"] for x in policies[group] if x["policy"]["name"] == value][0]  # Extract the right policy
                for key, value in mapping[programmatic_group].items()  # And convert the group to a nice name
            }
            for programmatic_group, group in groups_mapping.items()
        }
        # For some reason, some values are inverted, this code below "uninverts" them.
        return {
            group: {key: (value if key not in inverted_organisation_policy_settings else not value) for key, value in values.items()}
            for group, values in returned_mapping.items()
        }


class OrganisationBoardProcessSettings:
    @staticmethod
    def get_organisation_board_process_settings(ado_client: "AdoClient") -> dict[str, int]:
        PAYLOAD = build_hierarchy_payload(ado_client, "work-web.work-customization-hub-data-provider")
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/dataProviders/query?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()["data"]["ms.vss-work-web.work-customization-hub-data-provider"]["processes"]
        return {process["name"]: process["allProjectsCount"] for process in request}


class OrganisationPipelineSettings:
    @staticmethod
    def get_organisation_pipeline_settings(ado_client: "AdoClient") -> dict[str, bool]:
        PAYLOAD = build_hierarchy_payload(ado_client, "build-web.pipelines-org-settings-data-provider")
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()["dataProviders"]["ms.vss-build-web.pipelines-org-settings-data-provider"]
        # General, Triggers, Task Restrictions
        return {org_pipeline_settings_mapping[key]: value for key, value in request.items() if key in org_pipeline_settings_mapping}


@dataclass
class OrganisationRepositorySettings:
    programmatic_name: OrgRepoSettingsProgrammaticNamesTypes
    internal_name: OrgRepoSettingsInternalNamesTypes = field(repr=False)
    title: str
    description: str = field(repr=False)
    setting_enabled: bool  # If this setting is taking effect
    override_string_value: str | None  # For default_branch_name, an override string value
    default_value: str | None = field(repr=False)  # For default_branch_name, equal to "main" | None

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "OrganisationRepositorySettings":
        return cls(
            org_repo_settings_mapping[data["key"]],
            data["key"], data["title"], data["displayHtml"],
            data["value"], data["textValue"], data["defaultTextValue"])  # fmt: skip

    @classmethod
    def get_organisation_repository_settings(cls, ado_client: "AdoClient") -> list["OrganisationRepositorySettings"]:
        """From \n
        https://dev.azure.com/{ado_client.ado_org_name}/_settings/repositories"""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_api/_versioncontrol/AllGitRepositoriesOptions?__v=5"
        ).json()
        return [cls.from_request_payload(x) for x in request["__wrappedArray"]]

    @staticmethod
    def get_organisation_repository_advanced_settings(ado_client: "AdoClient") -> dict[str, bool]:
        """From \n
        https://dev.azure.com/{ado_client.ado_org_name}/_settings/repositories"""
        PAYLOAD = build_hierarchy_payload(
            ado_client, "advsec.advanced-security-enablement-data-provider", additional_properties={"givenProjectId": ""}
        )
        advanced_security_request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()["dataProviders"]["ms.vss-advsec.advanced-security-enablement-data-provider"]
        return {"automatically_enable_advanced_security_for_new_projects": advanced_security_request["enableOnCreate"]}

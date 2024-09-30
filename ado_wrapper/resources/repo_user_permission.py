from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.resources.users import AdoUser
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.errors import ResourceNotFound, InvalidPermissionsError
from ado_wrapper.utils import requires_initialisation, build_hierarchy_payload

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

PERMISSION_SET_ID = "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"  # This is global and hardcoded
RepoPermsActionType = Literal["Allow", "Deny", "Not set"]
RepoPermissionType = Literal[
    "manage_and_dismiss_alerts", "manage_settings", "view_alerts",
    "bypass_policies_when_completing_pull_requests", "bypass_policies_when_pushing", "contribute",
    "contribute_to_pull_requests", "create_branch", "create_tag", "delete_or_disable_repository",
    "edit_policies", "force_push", "manage_notes", "manage_permissions", "read", "remove_others_locks",
    "rename_repository",  # fmt: skip
]

external_to_internal_mapping: dict[str, RepoPermissionType] = {
    "Advanced Security: manage and dismiss alerts": "manage_and_dismiss_alerts",
    "Advanced Security: manage settings": "manage_settings",
    "Advanced Security: view alerts": "view_alerts",
    "Bypass policies when completing pull requests": "bypass_policies_when_completing_pull_requests",
    "Bypass policies when pushing": "bypass_policies_when_pushing",
    "Contribute": "contribute",
    "Contribute to pull requests": "contribute_to_pull_requests",
    "Create branch": "create_branch",
    "Create tag": "create_tag",
    "Delete or disable repository": "delete_or_disable_repository",
    "Edit policies": "edit_policies",
    "Force push (rewrite history, delete branches and tags)": "force_push",
    "Manage notes": "manage_notes",
    "Manage permissions": "manage_permissions",
    "Read": "read",
    "Remove others' locks": "remove_others_locks",
    "Rename repository": "rename_repository",
}

flag_mapping = {  # Where is 1 & 256?
    "manage_and_dismiss_alerts": 131072,
    "manage_settings": 262144,
    "view_alerts": 65536,
    "bypass_policies_when_completing_pull_requests": 32768,
    "bypass_policies_when_pushing": 128,
    "contribute": 4,
    "contribute_to_pull_requests": 16384,
    "create_branch": 16,
    "create_tag": 32,
    "delete_or_disable_repository": 512,
    "edit_policies": 2048,
    "force_push": 8,
    "manage_notes": 64,
    "manage_permissions": 8192,
    "read": 2,
    "remove_others_locks": 4096,
    "rename_repository": 1024,
}


@dataclass
class UserPermission:
    namespace_id: str = field(repr=False)
    display_name: str
    programmatic_name: RepoPermissionType
    token: str = field(repr=False)
    bit: int = field(repr=False)
    can_edit: bool = field(repr=False)
    permission_display_string: str

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "UserPermission":
        return cls(
            data["namespaceId"], data["displayName"], external_to_internal_mapping.get(data["displayName"], data["displayName"]),
            data["token"], data["bit"], data.get("canEdit", False), data["permissionDisplayString"]  # fmt: skip
        )

    @classmethod
    def get_by_subject_descriptor(cls, ado_client: "AdoClient", subject_descriptor: str, repo_id: str) -> list["UserPermission"]:
        requires_initialisation(ado_client)
        PAYLOAD = build_hierarchy_payload(
            ado_client, "admin-web.security-view-permissions-data-provider", additional_properties={
                "subjectDescriptor": subject_descriptor,
                "permissionSetId": PERMISSION_SET_ID,
                "permissionSetToken": f"repoV2/{ado_client.ado_project_id}/{repo_id}",
            },  # fmt: skip
        )
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=5.0-preview.1",
            json=PAYLOAD,
        ).json()["dataProviders"]["ms.vss-admin-web.security-view-permissions-data-provider"]
        if request is None:
            raise ResourceNotFound("Couldn't find perms for that repo, descriptor combo.")
        return [UserPermission.from_request_payload(x) for x in request["subjectPermissions"]]

    @classmethod
    def set_by_group_descriptor(cls, ado_client: "AdoClient", repo_id: str, group_descriptor: str, action: RepoPermsActionType, permission: RepoPermissionType) -> None:  # fmt: skip
        requires_initialisation(ado_client)
        IDENTITY_PAYLOAD = build_hierarchy_payload(
            ado_client, "admin-web.security-view-permissions-data-provider", additional_properties={
                "subjectDescriptor": group_descriptor,
                "permissionSetId": PERMISSION_SET_ID,
                "permissionSetToken": f"repoV2/{ado_client.ado_project_id}/{repo_id}",
            },  # fmt: skip
        )
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.0-preview.1",
            json=IDENTITY_PAYLOAD,
        ).json()
        identity_descriptor = request["dataProviders"]["ms.vss-admin-web.security-view-permissions-data-provider"]["identityDescriptor"]
        # ====
        PAYLOAD = {"token": f"repoV2/{ado_client.ado_project_id}/{repo_id}", "merge": True, "accessControlEntries": [
            {"descriptor": identity_descriptor,
             "allow": flag_mapping[permission] if action == "Allow" else 0, "deny": flag_mapping[permission] if action == "Deny" else 0}
        ]}  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/AccessControlEntries/{PERMISSION_SET_ID}",
            json=PAYLOAD,
        )
        if request.status_code == 403:
            raise InvalidPermissionsError("Cannot change the group's perms on this repo!")
        assert request.status_code == 200

    @classmethod
    def set_by_user_email(cls, ado_client: "AdoClient", repo_id: str, email: str, action: RepoPermsActionType,
                          permission: RepoPermissionType, domain_container_id: str = "") -> None:  # fmt: skip
        requires_initialisation(ado_client)
        if not domain_container_id:
            domain_container_id = AdoUser.get_by_email(ado_client, email).domain_container_id
        PAYLOAD = {"token": f"repoV2/{ado_client.ado_project_id}/{repo_id}", "merge": True, "accessControlEntries": [{
            "descriptor": f"Microsoft.IdentityModel.Claims.ClaimsIdentity;{domain_container_id}\\{email}",
            "allow": flag_mapping[permission] if action == "Allow" else 0, "deny": flag_mapping[permission] if action == "Deny" else 0,
        }]}  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/AccessControlEntries/{PERMISSION_SET_ID}",
            json=PAYLOAD,
        )
        if request.status_code == 403:
            raise InvalidPermissionsError("Cannot change the user's perms on this repo!")
        assert request.status_code == 200

    @classmethod
    def remove_perm(cls, ado_client: "AdoClient", repo_id: str, subject_email: str, domain_container_id: str = "") -> None:
        requires_initialisation(ado_client)
        if not domain_container_id:
            domain_container_id = AdoUser.get_by_email(ado_client, subject_email).domain_container_id
        token = f"repoV2/{ado_client.ado_project_id}/{repo_id}/&descriptors=Microsoft.IdentityModel.Claims.ClaimsIdentity;{domain_container_id}\\{subject_email}"
        request = ado_client.session.delete(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/AccessControlEntries/2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87?token={token}",
            json={"token": token},
        )
        assert request.status_code == 200


@dataclass
class RepoUserPermissions(StateManagedResource):
    @classmethod
    def get_all_by_repo_id(cls, ado_client: "AdoClient", repo_id: str, users_only: bool = True,
                           ignore_inherits: bool = True, remove_not_set: bool = False) -> dict[str, list[UserPermission]]:  # fmt: skip
        """Gets all user permissions for a repo, user_only removes groups.
        Returns a mapping of First Last: [UserPermission, UserPermission]"""
        requires_initialisation(ado_client)
        PAYLOAD = {"contributionIds": ["ms.vss-admin-web.security-view-members-data-provider"], "dataProviderContext": {"properties": {
            "permissionSetId": PERMISSION_SET_ID,
            "permissionSetToken": f"repoV2/{ado_client.ado_project_id}/{repo_id}"
        }}}  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.0-preview.1",
            json=PAYLOAD,
        ).json()["dataProviders"]["ms.vss-admin-web.security-view-members-data-provider"]
        if request is None:
            raise ResourceNotFound("Could not find any permissions for this repo! Does it exist?")
        # We now make descriptor -> display_name mapping
        groups_and_users = {
            identity["descriptor"]: identity["principalName"] if identity["subjectKind"] == "group" else identity["displayName"]
            for identity in request["identities"]
            if not users_only or (identity["subjectKind"] != "group")  # If we're doing users only, don't include if it's a group
        }  # fmt: skip
        # We then make user_name -> list[UserPermissions]
        perms_mapping = {
            name: UserPermission.get_by_subject_descriptor(ado_client, descriptor, repo_id)
            for descriptor, name in groups_and_users.items()  # fmt: skip
        }
        # Then, if they want to remove inherited perms, we do that.
        filtered_perms: dict[str, list[UserPermission]] = {
            user: perms for user, perms in perms_mapping.items() if not ignore_inherits or
            any(x.permission_display_string in ["Allow", "Deny"] for x in perms)  # fmt: skip
        }
        # Finally, if they want to remove perms which are left as "Not set", we do that now
        return {  # Filters Not set
            user: [x for x in perms if not remove_not_set or x.permission_display_string != ("Not set")]
            for user, perms in filtered_perms.items()
        }

    @staticmethod
    def get_by_subject_descriptor(ado_client: "AdoClient", repo_id: str, subject_descriptor: str) -> list[UserPermission]:
        return UserPermission.get_by_subject_descriptor(ado_client, subject_descriptor, repo_id)

    @classmethod
    def get_by_user_email(cls, ado_client: "AdoClient", repo_id: str, subject_email: str) -> list[UserPermission]:
        descriptor = AdoUser.get_by_email(ado_client, subject_email).descriptor_id
        return cls.get_by_subject_descriptor(ado_client, repo_id, descriptor)

    @staticmethod
    def set_by_group_descriptor(ado_client: "AdoClient", repo_id: str, group_descriptor: str, action: RepoPermsActionType, permission: RepoPermissionType) -> None:  # fmt: skip
        return UserPermission.set_by_group_descriptor(ado_client, repo_id, group_descriptor, action, permission)

    @staticmethod
    def set_by_user_email(ado_client: "AdoClient", repo_id: str, email: str, action: RepoPermsActionType,
                          permission: RepoPermissionType, domain_container_id: str = "") -> None:  # fmt: skip
        return UserPermission.set_by_user_email(ado_client, repo_id, email, action, permission, domain_container_id)

    @classmethod
    def set_by_user_email_batch(cls, ado_client: "AdoClient", repo_id: str, subject_email: str,
                                mapping: dict[RepoPermissionType, RepoPermsActionType], domain_container_id: str = "") -> None:  # fmt: skip
        """Does a batch job of updating permissions, updating all permissions for each user"""
        if not domain_container_id:
            domain_container_id = AdoUser.get_by_email(ado_client, subject_email).domain_container_id
        for permission, action in mapping.items():
            cls.set_by_user_email(ado_client, repo_id, subject_email, action, permission, domain_container_id)

    @classmethod
    def set_all_permissions_for_repo(cls, ado_client: "AdoClient", repo_id: str, mapping: dict[str, dict[RepoPermissionType, RepoPermsActionType]]) -> None:  # fmt: skip
        """Takes a mapping of <user_email>: {permission_name: Allow | Deny | Not set}}"""
        domain_container_id = AdoUser.get_by_email(ado_client, list(mapping.keys())[0]).domain_container_id
        for email, permission_pairs in mapping.items():
            cls.set_by_user_email_batch(ado_client, repo_id, email, permission_pairs, domain_container_id)

    @classmethod
    def remove_perm(cls, ado_client: "AdoClient", repo_id: str, subject_email: str, domain_container_id: str = "") -> None:
        return UserPermission.remove_perm(ado_client, repo_id, subject_email, domain_container_id)

    @staticmethod
    def display_output(permissions: list[UserPermission]) -> str:
        return "    " + "\n    ".join([str(x) for x in permissions])

    @staticmethod
    def display_output_for_repo(mapping: dict[str, list[UserPermission]]) -> str:
        return "\n".join([user_name + "\n" + RepoUserPermissions.display_output(values) for user_name, values in mapping.items()])

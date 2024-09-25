from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypedDict


if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

PermissionGroupLiteral = Literal[
    "Identity", "WorkItemTrackingAdministration", "DistributedTask", "WorkItemQueryFolders",
    "Git Repositories", "Registry", "VersionControlItems2", "EventSubscriber", "ServiceEndpoints"  # fmt: skip
]


class PermissionActionType(TypedDict):
    bit: int
    displayName: str


class PermissionType(TypedDict):
    namespaceId: str
    actions: list[PermissionActionType]


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #

permissions: dict[PermissionGroupLiteral, PermissionType] = {
    "Identity": {
        "namespaceId": "5a27515b-ccd7-42c9-84f1-54c998f03866",
        "actions": [
            {"bit": 1, "displayName": "View identity information"},
            {"bit": 2, "displayName": "Edit identity information"},
            {"bit": 4, "displayName": "Delete identity information"},
            {"bit": 8, "displayName": "Manage group membership"},
            {"bit": 16, "displayName": "Create identity scopes"},
        ],
    },
    "WorkItemTrackingAdministration": {
        "namespaceId": "445d2788-c5fb-4132-bbef-09c4045ad93f",
        "actions": [
            {"bit": 1, "displayName": "Manage permissions"},
            {"bit": 2, "displayName": "Destroy attachments"},
        ],
    },
    "DistributedTask": {
        "namespaceId": "101eae8c-1709-47f9-b228-0e476c35b3ba",
        "actions": [
            {"bit": 1, "displayName": "View"},
            {"bit": 2, "displayName": "Manage"},
            {"bit": 4, "displayName": "Listen"},
            {"bit": 8, "displayName": "Administer Permissions"},
            {"bit": 16, "displayName": "Use"},
            {"bit": 32, "displayName": "Create"},
        ],
    },
    "WorkItemQueryFolders": {
        "namespaceId": "71356614-aad7-4757-8f2c-0fb3bff6f680",
        "actions": [
            {"bit": 1, "displayName": "Read"},
            {"bit": 2, "displayName": "Contribute"},
            {"bit": 4, "displayName": "Delete"},
            {"bit": 8, "displayName": "Manage Permissions"},
            {"bit": 16, "displayName": "Full Control"},
        ],
    },
    "Git Repositories": {
        "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87",
        "actions": [
            {"bit": 1, "displayName": "Administer"},
            {"bit": 2, "displayName": "Read"},
            {"bit": 4, "displayName": "Contribute"},
            {"bit": 8, "displayName": "Force push (rewrite history and delete branches)"},
            {"bit": 16, "displayName": "Create branch"},
            {"bit": 32, "displayName": "Create tag"},
            {"bit": 64, "displayName": "Manage notes"},
            {"bit": 128, "displayName": "Bypass policies when pushing"},
            {"bit": 256, "displayName": "Create repository"},
            {"bit": 512, "displayName": "Delete repository"},
            {"bit": 1024, "displayName": "Rename repository"},
            {"bit": 2048, "displayName": "Edit policies"},
            {"bit": 4096, "displayName": "Remove others' locks"},
            {"bit": 8192, "displayName": "Manage permissions"},
            {"bit": 16384, "displayName": "Contribute to pull requests"},
            {"bit": 32768, "displayName": "Bypass policies when completing pull requests"},
            {"bit": 65536, "displayName": "Advanced Security: view alerts"},
            {"bit": 131072, "displayName": "Advanced Security: manage and dismiss alerts"},
            {"bit": 262144, "displayName": "Advanced Security: manage settings"},
        ],
    },
    "Registry": {
        "namespaceId": "4ae0db5d-8437-4ee8-a18b-1f6fb38bd34c",
        "actions": [
            {"bit": 1, "displayName": "Read registry entries"},
            {"bit": 2, "displayName": "Write registry entries"},
        ],
    },
    "VersionControlItems2": {
        "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e",
        "actions": [
            {"bit": 1, "displayName": "Read"},
            {"bit": 2, "displayName": "Pend a change in a server workspace"},
            {"bit": 4, "displayName": "Check in"},
            {"bit": 8, "displayName": "Label"},
            {"bit": 16, "displayName": "Lock"},
            {"bit": 32, "displayName": "Revise other users' changes"},
            {"bit": 64, "displayName": "Unlock other users' changes"},
            {"bit": 128, "displayName": "Undo other users' changes"},
            {"bit": 256, "displayName": "Administer labels"},
            {"bit": 1024, "displayName": "Manage permissions"},
            {"bit": 2048, "displayName": "Check in other users' changes"},
            {"bit": 4096, "displayName": "Merge"},
            {"bit": 8192, "displayName": "Manage branch"},
        ],
    },
    "EventSubscriber": {
        "namespaceId": "2bf24a2b-70ba-43d3-ad97-3d9e1f75622f",
        "actions": [
            {"bit": 1, "displayName": "View"},
            {"bit": 2, "displayName": "Edit"},
        ],
    },
    "ServiceEndpoints": {
        "namespaceId": "49b48001-ca20-4adc-8111-5b60c903a50c",
        "actions": [
            {"bit": 1, "displayName": "Use Endpoint"},
            {"bit": 2, "displayName": "Administer Endpoint"},
            {"bit": 4, "displayName": "Create Endpoint"},
            {"bit": 8, "displayName": "View Authorization"},
            {"bit": 16, "displayName": "View Endpoint"},
        ],
    },
}
# This is broken for some reason, please leave it commented out :)
# "WorkItemTrackingProvision": {
#   "namespaceId": "5a6cd233-6615-414d-9393-48dbb252bd23",
#   "actions": [
#     {"bit": 1, "displayName": "Administer"},
#     {"bit": 2, "displayName": "Manage work item link types"},
#   ],
# },

namespace_id_to_group: dict[str, PermissionGroupLiteral] = {
    value["namespaceId"]: key for key, value in permissions.items()
}  # fmt: skip

namespace_id_to_perm: dict[tuple[str, int], PermissionActionType] = {  # Mapping of `(sec_namespace, bit)` to `action`
    (value["namespaceId"], action["bit"]): action for value in permissions.values()
    for action in value["actions"]
}  # fmt: skip

# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #


@dataclass
class Permission:
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/security/permissions/has-permissions-batch?view=azure-devops-rest-7.1"""

    group: PermissionGroupLiteral
    group_namespace_id: str = field(repr=False)
    name: str
    bit: int = field(repr=False)
    has_permission: bool

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Permission":
        security_namespace = data["securityNamespaceId"]
        action = namespace_id_to_perm[(security_namespace), data["permissions"]]
        return cls(
            namespace_id_to_group[security_namespace], security_namespace,
            action["displayName"], action["bit"], data["value"]  # fmt: skip
        )

    @classmethod
    def get_project_perms(cls, ado_client: "AdoClient") -> list["Permission"]:
        """Returns a list of permissions (with has_permission set to True if the perms have been granted) for the given
        Public Access Token (PAT) passed in to the client."""
        PAYLOAD = {
            "evaluations": [
                {"securityNamespaceId": perm_group["namespaceId"], "token": f"repoV2/{ado_client.ado_project_id}", "permissions": action["bit"]}
                for perm_group in permissions.values()
                for action in perm_group["actions"]
            ]
        }  # fmt: skip
        request = ado_client.session.post(  # Post, so can't use super()._get_by_url
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/security/permissionevaluationbatch?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()
        return [cls.from_request_payload(x) for x in request["evaluations"]]

    @classmethod
    def get_project_perms_by_group(cls, ado_client: "AdoClient", group: PermissionGroupLiteral) -> list["Permission"]:
        return [x for x in cls.get_project_perms(ado_client) if x.group == group]

    @staticmethod
    def print_perms(ado_client: "AdoClient") -> None:
        print("\n".join([str(x) for x in Permission.get_project_perms(ado_client)]))


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #

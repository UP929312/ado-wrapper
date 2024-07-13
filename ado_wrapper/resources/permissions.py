from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypedDict


if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

PermissionGroupLiteral = Literal[
    "Identity", "WorkItemTrackingAdministration", "DistributedTask", "WorkItemQueryFolders",
    "Git Repositories", "Registry", "VersionControlItems2", "EventSubscriber", "ServiceEndpoints"  # fmt: skip
]


class ActionType(TypedDict):
    bit: int
    displayName: str
    namespaceId: str


class PermissionType(TypedDict):
    namespaceId: str
    actions: list[ActionType]


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #

permissions: dict[PermissionGroupLiteral, PermissionType] = {
    "Identity": {
      "namespaceId": "5a27515b-ccd7-42c9-84f1-54c998f03866",
      "actions": [
        {
          "bit": 1,
          "displayName": "View identity information",
          "namespaceId": "5a27515b-ccd7-42c9-84f1-54c998f03866"
        },
        {
          "bit": 2,
          "displayName": "Edit identity information",
          "namespaceId": "5a27515b-ccd7-42c9-84f1-54c998f03866"
        },
        {
          "bit": 4,
          "displayName": "Delete identity information",
          "namespaceId": "5a27515b-ccd7-42c9-84f1-54c998f03866"
        },
        {
          "bit": 8,
          "displayName": "Manage group membership",
          "namespaceId": "5a27515b-ccd7-42c9-84f1-54c998f03866"
        },
        {
          "bit": 16,
          "displayName": "Create identity scopes",
          "namespaceId": "5a27515b-ccd7-42c9-84f1-54c998f03866"
        }
      ],
    },
    "WorkItemTrackingAdministration": {
      "namespaceId": "445d2788-c5fb-4132-bbef-09c4045ad93f",
      "actions": [
        {
          "bit": 1,
          "displayName": "Manage permissions",
          "namespaceId": "445d2788-c5fb-4132-bbef-09c4045ad93f"
        },
        {
          "bit": 2,
          "displayName": "Destroy attachments",
          "namespaceId": "445d2788-c5fb-4132-bbef-09c4045ad93f"
        }
      ],
    },
    "DistributedTask": {
      "namespaceId": "101eae8c-1709-47f9-b228-0e476c35b3ba",
      "actions": [
        {
          "bit": 1,
          "displayName": "View",
          "namespaceId": "101eae8c-1709-47f9-b228-0e476c35b3ba"
        },
        {
          "bit": 2,
          "displayName": "Manage",
          "namespaceId": "101eae8c-1709-47f9-b228-0e476c35b3ba"
        },
        {
          "bit": 4,
          "displayName": "Listen",
          "namespaceId": "101eae8c-1709-47f9-b228-0e476c35b3ba"
        },
        {
          "bit": 8,
          "displayName": "Administer Permissions",
          "namespaceId": "101eae8c-1709-47f9-b228-0e476c35b3ba"
        },
        {
          "bit": 16,
          "displayName": "Use",
          "namespaceId": "101eae8c-1709-47f9-b228-0e476c35b3ba"
        },
        {
          "bit": 32,
          "displayName": "Create",
          "namespaceId": "101eae8c-1709-47f9-b228-0e476c35b3ba"
        }
      ],
    },
    "WorkItemQueryFolders": {
      "namespaceId": "71356614-aad7-4757-8f2c-0fb3bff6f680",
      "actions": [
        {
          "bit": 1,
          "displayName": "Read",
          "namespaceId": "71356614-aad7-4757-8f2c-0fb3bff6f680"
        },
        {
          "bit": 2,
          "displayName": "Contribute",
          "namespaceId": "71356614-aad7-4757-8f2c-0fb3bff6f680"
        },
        {
          "bit": 4,
          "displayName": "Delete",
          "namespaceId": "71356614-aad7-4757-8f2c-0fb3bff6f680"
        },
        {
          "bit": 8,
          "displayName": "Manage Permissions",
          "namespaceId": "71356614-aad7-4757-8f2c-0fb3bff6f680"
        },
        {
          "bit": 16,
          "displayName": "Full Control",
          "namespaceId": "71356614-aad7-4757-8f2c-0fb3bff6f680"
        }
      ],
    },
    "Git Repositories": {
      "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87",
      "actions": [
        {
          "bit": 1,
          "displayName": "Administer",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 2,
          "displayName": "Read",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 4,
          "displayName": "Contribute",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 8,
          "displayName": "Force push (rewrite history and delete branches)",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 16,
          "displayName": "Create branch",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 32,
          "displayName": "Create tag",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 64,
          "displayName": "Manage notes",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 128,
          "displayName": "Bypass policies when pushing",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 256,
          "displayName": "Create repository",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 512,
          "displayName": "Delete repository",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 1024,
          "displayName": "Rename repository",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 2048,
          "displayName": "Edit policies",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 4096,
          "displayName": "Remove others' locks",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 8192,
          "displayName": "Manage permissions",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 16384,
          "displayName": "Contribute to pull requests",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 32768,
          "displayName": "Bypass policies when completing pull requests",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 65536,
          "displayName": "Advanced Security: view alerts",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 131072,
          "displayName": "Advanced Security: manage and dismiss alerts",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        },
        {
          "bit": 262144,
          "displayName": "Advanced Security: manage settings",
          "namespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        }
      ],
    },
    "Registry": {
      "namespaceId": "4ae0db5d-8437-4ee8-a18b-1f6fb38bd34c",
      "actions": [
        {
          "bit": 1,
          "displayName": "Read registry entries",
          "namespaceId": "4ae0db5d-8437-4ee8-a18b-1f6fb38bd34c"
        },
        {
          "bit": 2,
          "displayName": "Write registry entries",
          "namespaceId": "4ae0db5d-8437-4ee8-a18b-1f6fb38bd34c"
        }
      ],
    },
    "VersionControlItems2": {
      "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e",
      "actions": [
        {
          "bit": 1,
          "displayName": "Read",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 2,
          "displayName": "Pend a change in a server workspace",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 4,
          "displayName": "Check in",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 8,
          "displayName": "Label",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 16,
          "displayName": "Lock",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 32,
          "displayName": "Revise other users' changes",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 64,
          "displayName": "Unlock other users' changes",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 128,
          "displayName": "Undo other users' changes",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 256,
          "displayName": "Administer labels",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 1024,
          "displayName": "Manage permissions",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 2048,
          "displayName": "Check in other users' changes",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 4096,
          "displayName": "Merge",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        },
        {
          "bit": 8192,
          "displayName": "Manage branch",
          "namespaceId": "3c15a8b7-af1a-45c2-aa97-2cb97078332e"
        }
      ],
    },
   "EventSubscriber":  {
      "namespaceId": "2bf24a2b-70ba-43d3-ad97-3d9e1f75622f",
      "actions": [
        {
          "bit": 1,
          "displayName": "View",
          "namespaceId": "2bf24a2b-70ba-43d3-ad97-3d9e1f75622f"
        },
        {
          "bit": 2,
          "displayName": "Edit",
          "namespaceId": "2bf24a2b-70ba-43d3-ad97-3d9e1f75622f"
        }
      ],
    },
    # This is broken for some reason, please leave it commented out :)
    # "WorkItemTrackingProvision": {
    #   "namespaceId": "5a6cd233-6615-414d-9393-48dbb252bd23",
    #   "actions": [
    #     {
    #       "bit": 1,
    #       "displayName": "Administer",
    #       "namespaceId": "5a6cd233-6615-414d-9393-48dbb252bd23"
    #     },
    #     {
    #       "bit": 2,
    #       "displayName": "Manage work item link types",
    #       "namespaceId": "5a6cd233-6615-414d-9393-48dbb252bd23"
    #     }
    #   ],
    # },
    "ServiceEndpoints": {
      "namespaceId": "49b48001-ca20-4adc-8111-5b60c903a50c",
      "actions": [
        {
          "bit": 1,
          "displayName": "Use Endpoint",
          "namespaceId": "49b48001-ca20-4adc-8111-5b60c903a50c"
        },
        {
          "bit": 2,
          "displayName": "Administer Endpoint",
          "namespaceId": "49b48001-ca20-4adc-8111-5b60c903a50c"
        },
        {
          "bit": 4,
          "displayName": "Create Endpoint",
          "namespaceId": "49b48001-ca20-4adc-8111-5b60c903a50c"
        },
        {
          "bit": 8,
          "displayName": "View Authorization",
          "namespaceId": "49b48001-ca20-4adc-8111-5b60c903a50c"
        },
        {
          "bit": 16,
          "displayName": "View Endpoint",
          "namespaceId": "49b48001-ca20-4adc-8111-5b60c903a50c"
        }
      ],
    },
}  # fmt: skip

namespace_id_to_group: dict[str, PermissionGroupLiteral] = {
    value["namespaceId"]: key for key, value in permissions.items()
}  # fmt: skip
namespace_id_to_perm: dict[tuple[str, int], ActionType] = {  # Mapping of `(sec_namespace, bit)` to `action`
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
    namespace_id: str = field(repr=False)
    has_permission: bool

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> Permission:
        security_namespace = data["securityNamespaceId"]
        action = namespace_id_to_perm[(security_namespace), data["permissions"]]
        return cls(
            namespace_id_to_group[security_namespace], security_namespace,
            action["displayName"], action["bit"], action["namespaceId"], data["value"]  # fmt: skip
        )

    @classmethod
    def get_project_perms(cls, ado_client: AdoClient) -> list[Permission]:
        """Returns a list of permissions (with has_permission set to True if the perms have been granted) for the given
        Public Access Token (PAT) passed in to the client."""
        PAYLOAD = {
            "evaluations": [
                {"securityNamespaceId": perm_group["namespaceId"], "token": f"repoV2/{ado_client.ado_project_id}", "permissions": action["bit"]}
                for perm_group in permissions.values()
                for action in perm_group["actions"]
            ]
        }  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org}/_apis/security/permissionevaluationbatch?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()
        return [cls.from_request_payload(x) for x in request["evaluations"]]

    @classmethod
    def get_project_perms_by_group(cls, ado_client: AdoClient, group: PermissionGroupLiteral) -> list[Permission]:
        return [x for x in cls.get_project_perms(ado_client) if x.group == group]


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #

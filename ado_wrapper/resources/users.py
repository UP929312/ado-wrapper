from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.state_managed_abc import StateManagedResource

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

PROPERTIES_FOR_SEARCH = [
    "DisplayName", "ScopeName", "SamAccountName", "Active", "SubjectDescriptor", "Department",
    "JobTitle", "Mail", "MailNickname", "SignInAddress",
]  # fmt: skip

VOTE_ID_TO_TYPE = {
    10: "approved",
    5: "approved with suggestions",
    0: "no vote",
    -5: "waiting for author",
    -10: "rejected",
}
VoteOptions = Literal[10, 5, 0, -5, -10]

# ======================================================================================================= #


@dataclass
class AdoUser(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/graph/users?view=azure-devops-rest-7.1"""

    descriptor_id: str = field(metadata={"is_id_field": True})
    display_name: str
    email: str
    origin: str
    origin_id: str  # NORMALLY DON'T USE THIS, USE `descriptor_id` INSTEAD
    domain_container_id: str  # Ignore this
    # "subjectKind": "user",
    # "metaType": "member",
    # "directoryAlias": "surnameF",
    # "url": "https://vssps.dev.azure.com/{ado_client.}/_apis/Graph/Users/aad.M2Q5NDlkZTgtZDI2Yi03MGQ3LWEyYjItMDAwYTQzYTdlNzFi",

    def __str__(self) -> str:
        return f"{self.display_name} ({self.email})"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "AdoUser":
        return cls(
            data["descriptor"], data["displayName"], data["mailAddress"].removeprefix("vstfs:///Classification/TeamProject/"),
            data["origin"], data["originId"], data.get("domain", "UNKNOWN")
        )  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", descriptor_id: str) -> "AdoUser":
        return super()._get_by_url(
            ado_client,  # Preview required
            f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/graph/users/{descriptor_id}?api-version=7.1-preview.1",
        )

    @classmethod
    def create(cls, ado_client: "AdoClient", member_name: str, member_email: str) -> "AdoUser":
        raise NotImplementedError("Creating a new user is not supported")

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", member_id: str) -> None:
        raise NotImplementedError("Deleting a user is not supported")

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["AdoUser"]:
        return super()._get_all(
            ado_client,  # Preview required
            f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/graph/users?api-version=7.1-preview.1",
        )  # pyright: ignore[reportReturnType]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_email(cls, ado_client: "AdoClient", member_email: str) -> "AdoUser":
        user = cls._get_by_abstract_filter(ado_client, lambda user: user.email == member_email)
        if user is None:
            raise ValueError(f"Member with email {member_email} not found")
        return user

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "AdoUser | None":
        return cls._get_by_abstract_filter(ado_client, lambda user: user.display_name == name)

    @classmethod
    def get_by_descriptor_id(cls, ado_client: "AdoClient", descriptor_id: str) -> "AdoUser | None":
        return cls._get_by_abstract_filter(ado_client, lambda user: user.descriptor_id == descriptor_id)

    @classmethod
    def get_by_origin_id(cls, ado_client: "AdoClient", origin_id: str) -> "AdoUser | None":
        return cls._get_by_abstract_filter(ado_client, lambda user: user.origin_id == origin_id)

    @classmethod
    def search_by_query(cls, ado_client: "AdoClient", query: str) -> dict[str, str]:
        """Returns a user to identity, query is email, first name, etc Essentially when using a search bar, what you'll get in return."""
        PAYLOAD = {"query": query, "identityTypes": ["user", "group"], "operationScopes": ["ims", "source"],
                   "options": {"MinResults": 5, "MaxResults": 25}, "properties": PROPERTIES_FOR_SEARCH}  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/IdentityPicker/Identities?api-version=7.0-preview.1",
            json=PAYLOAD,
        ).json()
        return request["results"][0]["identities"][0]  # type: ignore[no-any-return]

    @staticmethod
    def _convert_local_ids_to_origin_ids(ado_client: "AdoClient", local_ids: list[str]) -> dict[str, str]:
        """Converts a mapping of local_ids to origin_ids"""
        local_to_descriptor = {}
        for local_id in local_ids:
            request = ado_client.session.get(
                f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/graph/descriptors/{local_id}?api-version=7.0-preview.1"
            ).json()
            local_to_descriptor[local_id] = request["value"]
        # Now get a mapping of local_ids to origin_ids
        mapping = {}
        for local_id, descriptor_id in local_to_descriptor.items():
            mapping[local_id] = AdoUser.get_by_descriptor_id(ado_client, descriptor_id).origin_id  # type: ignore[union-attr]
        return mapping

    @staticmethod
    def _convert_origin_ids_to_local_ids(ado_client: "AdoClient", origin_ids: list[str]) -> dict[str, str]:
        """Converts a mapping of origin_ids to local_ids"""
        user_objects: list[AdoUser] = [AdoUser.get_by_origin_id(ado_client, x) for x in origin_ids]  # type: ignore[misc]
        return {identity.origin_id: AdoUser.search_by_query(ado_client, identity.email)["localId"]
                for identity in user_objects}  # fmt: skip

    # @staticmethod
    # def _convert_descriptor_ids_to_local_ids(ado_client: "AdoClient", descriptor_ids: list[str]) -> dict[str, str]:
    #     """Converts a mapping of descriptor_ids to local_ids"""
    #     user_objects: list[AdoUser] = [AdoUser.get_by_descriptor_id(ado_client, x) for x in descriptor_ids]  # type: ignore[assignment]
    #     return {identity.descriptor_id: AdoUser.search_by_query(ado_client, identity.email)["localId"] for identity in user_objects}

    # @classmethod
    # def convert_origin_id_to_descriptors(cls, ado_client: "AdoClient", origin_ids: list[str]) -> dict[str, str]:
    #     all_users = cls.get_all(ado_client)
    #     mapping = {user.origin_id: user.descriptor_id for user in all_users if user.origin_id in origin_ids}
    #     return mapping


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #


@dataclass
class Member(StateManagedResource):
    """A stripped down member class which is often returned by the API, for example in build requests or PRs."""

    name: str
    email: str
    member_id: str = field(metadata={"is_id_field": True}, repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Member":
        # displayName, uniqueName/mailAddress, id/originId
        # This gets returned slightly differently from different APIs
        return cls(
            data["displayName"],
            data.get("uniqueName") or data.get("mailAddress", "UNKNOWN"),  # type: ignore[arg-type]
            data.get("id") or data["originId"],
        )  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", member_id: str) -> "Member":
        raise NotImplementedError("Getting a member by ID is not supported")

    @classmethod
    def create(cls, ado_client: "AdoClient", member_name: str, member_email: str) -> "Member":
        raise NotImplementedError("Creating a new member is not supported")

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", member_id: str) -> None:
        raise NotImplementedError("Deleting a member is not supported")


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #


class TeamMember(Member):
    """Identical to Member, but with an additional attribute `is_team_admin`."""

    def __init__(self, name: str, email: str, member_id: str, is_team_admin: bool) -> None:
        super().__init__(name, email, member_id)
        self.is_team_admin = is_team_admin  # Static

    def __str__(self) -> str:
        return f"{super().__str__()}" + (" (Team Admin)" if self.is_team_admin else "")

    def __repr__(self) -> str:
        return f"{super().__str__().removesuffix(')')}, team_admin={self.is_team_admin})"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "TeamMember":
        return cls(data["name"], data["email"], data["id"], data["is_team_admin"])

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name, "email": self.email, "id": self.member_id, "is_team_admin": self.is_team_admin,  # fmt: skip
        }

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "TeamMember":
        return cls(data["identity"]["displayName"], data["identity"]["uniqueName"], data["identity"]["id"], data.get("isTeamAdmin", False))


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #


class Reviewer(Member):
    """Identical to Member, but with additional attributes `vote` and `is_required` for PR reviews."""

    def __init__(self, name: str, email: str, reviewer_id: str, vote: VoteOptions = 0, is_required: bool = False) -> None:
        super().__init__(name, email, reviewer_id)
        self.vote = vote
        self.is_required = is_required

    def __str__(self) -> str:
        return f'{self.name} ({self.email}) voted {VOTE_ID_TO_TYPE[self.vote]}, and was {"required" if self.is_required else "optional"}'

    def __repr__(self) -> str:
        return f"Reviewer(name={self.name}, email={self.email}, id={self.member_id}, vote={self.vote}, is_required={self.is_required})"

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "id": self.member_id,
            "vote": self.vote,
            "is_required": self.is_required,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Reviewer":
        return cls(data["name"], data["email"], data["id"], data["vote"], data.get("isRequired", False))

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Reviewer":
        return cls(data["displayName"], data["uniqueName"], data["id"], data["vote"], data.get("isRequired", False))


# ======================================================================================================= #

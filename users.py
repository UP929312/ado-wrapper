from __future__ import annotations

from typing import Literal, Any, TYPE_CHECKING

import requests

from state_managed_abc import StateManagedResource

if TYPE_CHECKING:
    from client import AdoClient

VOTE_ID_TO_TYPE = {
    10: "approved",
    5: "approved with suggestions",
    0: "no vote",
    -5: "waiting for author",
    -10: "rejected",
}
VoteOptions = Literal[10, 5, 0, -5, -10]

# ======================================================================================================= #


class AdoUser(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/graph/users?view=azure-devops-rest-7.1"""
    def __init__(self, descriptor_id: str, name: str, email: str, origin: str) -> None:
        self.descriptor_id = descriptor_id  # Static
        self.display_name = name  # Static
        self.email = email.removeprefix("vstfs:///Classification/TeamProject/")  # Static
        self.origin = origin  # Static
        # "originId": "<>",
        # "subjectKind": "user",
        # "metaType": "member",
        # "directoryAlias": "MiryabblliS",
        # "domain": "68283f3b-8487-4c86-adb3-a5228f18b893",
        # "url": "https://vssps.dev.azure.com/vfuk-digital/_apis/Graph/Users/aad.M2Q5NDlkZTgtZDI2Yi03MGQ3LWEyYjItMDAwYTQzYTdlNzFi",

    def __str__(self) -> str:
        return f"{self.display_name} ({self.email})"

    def __repr__(self) -> str:
        return f"Member(display_name={self.display_name}, email={self.email}, id={self.descriptor_id}, origin={self.origin})"

    def to_json(self) -> dict[str, Any]:
        return {
            "descriptor_id": self.descriptor_id,
            "display_name": self.display_name,
            "email": self.email,
            "origin": self.origin,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "AdoUser":
        return cls(data["member_id"], data["display_name"], data["email"], data["origin"])

    @classmethod
    def from_request_payload(cls, data: dict[str, str]) -> "AdoUser":
        return cls(data["descriptor"], data["displayName"], data["mailAddress"], data["origin"])

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, descriptor_id: str) -> "AdoUser":
        request = requests.get(
            f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/graph/users/{descriptor_id}?api-version=6.0-preview.1",
            auth=ado_client.auth,
        ).json()
        return cls.from_request_payload(request)

    @classmethod
    def create(cls, ado_client: AdoClient, member_name: str, member_email: str) -> "AdoUser":
        raise NotImplementedError("Creating a new user is not supported")

    @staticmethod
    def delete_by_id(ado_client: AdoClient, member_id: str) -> None:
        raise NotImplementedError("Deleting a user is not supported")

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["AdoUser"]:
        request = requests.get(
            f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/graph/users?api-version=7.1-preview.1", auth=ado_client.auth
        ).json()
        return [cls.from_request_payload(member) for member in request["value"]]

    @classmethod
    def get_by_email(cls, ado_client: AdoClient, member_email: str) -> "AdoUser":
        for member in cls.get_all(ado_client):
            if member.email == member_email:
                return member
        raise ValueError(f"Member with email {member_email} not found")

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, member_name: str) -> "AdoUser":
        for member in cls.get_all(ado_client):
            if member.display_name == member_name:
                return member
        raise ValueError(f"Member with name {member_name} not found")

    def delete(self, ado_client: AdoClient) -> None:
        self.delete_by_id(ado_client, self.descriptor_id)


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #


class Member:
    """A stripped down member class which is often returned by the API, for example in build requests."""

    def __init__(self, name: str, email: str, member_id: str) -> None:
        self.name = name  # Static
        self.email = email.removeprefix("vstfs:///Classification/TeamProject/")  # Static
        self.member_id = member_id  # Static

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"

    def __repr__(self) -> str:
        return f"Commiter({self.name}, {self.email})"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Member":
        return cls(data["name"], data["email"], data["id"])

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "id": self.member_id,
        }

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Member":
        return cls(data["displayName"], data["mailAddress"], data["originId"])


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
        return f"{super().__str__()[:-1]}, team_admin={self.is_team_admin})"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "TeamMember":
        return cls(data["name"], data["email"], data["id"], data["is_team_admin"])

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "id": self.member_id,
            "is_team_admin": self.is_team_admin,
        }

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "TeamMember":
        return cls(data["identity"]["displayName"], data["identity"]["uniqueName"], data["identity"]["id"], data.get("isTeamAdmin", False))


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #


class Reviewer(Member):
    """Identical to Member, but with additional attributes `vote` and `is_required` for PR reviews."""

    def __init__(self, name: str, email: str, reviewer_id: str, vote: VoteOptions, is_required: bool) -> None:
        super().__init__(name, email, reviewer_id)
        self.vote = vote  # Static
        self.is_required = is_required  # Static

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
        return cls(data["name"], data["email"], data["id"], data["vote"], data["isRequired"])

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Reviewer":
        return cls(data["displayName"], data["uniqueName"], data["id"], data["vote"], data.get("isRequired", False))


# ======================================================================================================= #

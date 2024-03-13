from typing import Literal, Any, TYPE_CHECKING

# import requests

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

# ========================================================================================================


class Member:
    def __init__(self, name: str, email: str, member_id: str) -> None:
        self.name = name
        self.email = email.removeprefix("vstfs:///Classification/TeamProject/")
        self.member_id = member_id

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"

    def __repr__(self) -> str:
        return f"Member({self.name}, {self.email})"

    @classmethod
    def from_json(cls, data: dict[str, str]) -> "Member":
        return cls(data["displayName"], data["mailAddress"], data["id"])

    # @classmethod  # We don't have vssps (identity) access, so we can't use this
    # def get_by_id(cls, ado_helper: AdoHelper, member_id: str) -> "Member":
    #     request = requests.get(f"https://vssps.dev.azure.com/{ado_helper.ado_org}/_apis/graph/users/{member_id}?api-version=6.0", auth=ado_helper.auth).json()
    #     return cls.from_json(request)

    # @classmethod  # We don't have vssps (identity) access, so we can't use this
    # def get_all(cls, ado_helper: AdoHelper) -> list["Member"]:
    #     request = requests.get(f"https://vssps.dev.azure.com/{ado_helper.ado_org}/_apis/graph/users?api-version=7.1-preview.1", auth=ado_helper.auth).json()
    #     print(request.status_code, request.text)
    #     return [cls.from_json(member) for member in request["value"]]

    # @classmethod  # We don't have vssps (identity) access, so we can't use this
    # def get_by_email(cls, ado_helper: AdoHelper, member_name: str) -> "Member":
    #     all_members = cls.get_all_members(ado_helper)
    #     our_user = [member for member in all_members if member.email == member_name]
    #     if not our_user:
    #         raise ValueError(f"Member {member_name} not found")
    #     return our_user[0]


# ========================================================================================================


class Reviewer(Member):
    def __init__(self, name: str, email: str, reviewer_id: str, vote: VoteOptions, is_required: bool) -> None:
        super().__init__(name, email, reviewer_id)
        self.vote = vote
        self.is_required = is_required

    def __str__(self) -> str:
        return f'{self.name} ({self.email}) voted {VOTE_ID_TO_TYPE[self.vote]}, and was {"required" if self.is_required else "optional"}'

    def __repr__(self) -> str:
        return f"Reviewer(name={self.name}, email={self.email}, id={self.member_id}, vote={self.vote}, is_required={self.is_required})"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Reviewer":
        return cls(data["displayName"], data["uniqueName"], data["id"], data["vote"], data.get("isRequired", False))


# ========================================================================================================

if __name__ == "__main__":
    from secret import email, ado_access_token, ado_org, ado_project
    from client import AdoClient

    ado_helper = AdoClient(email, ado_access_token, ado_org, ado_project)
    # print(Member.get_all_members(ado_helper))
    # print(Member.get_by_email(ado_helper, email))
    # print(Member.get_by_id(ado_helper, ))

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ado_wrapper.resources.users import TeamMember
from ado_wrapper.state_managed_abc import StateManagedResource

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


@dataclass
class Team(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/core/teams?view=azure-devops-rest-7.1
    Team members are only set when using the get_by_id method. They are not set when using the get_all method."""

    team_id: str = field(metadata={"is_id_field": True})  # None are editable
    name: str
    description: str
    team_members: list[TeamMember] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.name} ({self.team_id}" + (", ".join([str(member) for member in self.team_members])) + ")"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Team":
        return cls(data["id"], data["name"], data.get("description", ""), [])

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", team_id: str) -> "Team":
        resource: Team = super()._get_by_url(
            ado_client,
            f"/_apis/projects/{ado_client.ado_project_name}/teams/{team_id}?$expandIdentity={True}&api-version=7.1-preview.1",
        )
        resource.team_members = resource.get_members(ado_client)
        return resource

    @classmethod
    def create(cls, ado_client: "AdoClient", name: str, description: str) -> "Team":
        return super()._create(
            ado_client,
            f"/_apis/projects/{ado_client.ado_project_name}/teams?api-version=7.1",
            {"name": name, "description": description},
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", team_id: str) -> None:
        return super()._delete_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/projects/{ado_client.ado_project_name}/teams/{team_id}?api-version=7.1",
            team_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["Team"]:
        return super()._get_all(
            ado_client,
            "/_apis/teams?api-version=7.1-preview.2",
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_settings/teams?subjectDescriptor=v{self.team_id}"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", team_name: str) -> "Team | None":
        return cls._get_by_abstract_filter(ado_client, lambda team: team.name == team_name)

    def get_members(self, ado_client: "AdoClient") -> list[TeamMember]:
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/projects/{ado_client.ado_project_name}/teams/{self.team_id}/members?api-version=7.1-preview.2",
        ).json()
        if "value" not in request and request.get("message", "").startswith("The team with id "):  # If the team doesn't exist anymore.
            return []
        team_members = [TeamMember.from_request_payload(member) for member in request["value"]]
        self.team_members = team_members
        return team_members

    # @staticmethod
    # def _recursively_extract_teams(ado_client: "AdoClient", team_or_member: Team | TeamMember):
    #     if isinstance(team_or_member, Team):
    #         rint("Found a team!")
    #         team_or_member.get_members(ado_client)
    #         for member in team_or_member.team_members:
    #             Team._recursively_extract_teams(ado_client, member)
    #     return team_or_member

    # @classmethod
    # def get_all_teams_recursively(cls, ado_client: "AdoClient") -> list["TeamMember | Team"]:
    #     all_teams = [
    #         cls._recursively_extract_teams(ado_client, team)
    #         for team in cls.get_all(ado_client)
    #     ]
    #     return all_teams

    # """
    # The output should be as follows:
    # [
    #     Team 1 = [
    #         TeamMember 1,
    #         TeamMember 2,
    #         TeamMember 3
    #     ],
    #     Team 2 = [
    #         TeamMember 4,
    #         Team 3 = [
    #             TeamMember 5,
    #             TeamMember 6
    #         ]
    #     ],
    # ]
    # """

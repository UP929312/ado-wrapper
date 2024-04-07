from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass, field

import requests

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import TeamMember

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
    def from_request_payload(cls, data: dict[str, str]) -> "Team":
        return cls(data["id"], data["name"], data.get("description", ""), [])

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, team_id: str) -> "Team":
        resource: Team = super().get_by_id(
            ado_client,
            f"/_apis/projects/{ado_client.ado_project}/teams/{team_id}?$expandIdentity={True}&api-version=7.1-preview.1",
        )  # type: ignore[assignment]
        resource.team_members = resource.get_members(ado_client)
        return resource

    @classmethod
    def create(cls, ado_client: AdoClient, name: str, description: str) -> "Team":  # type: ignore[override]
        raise NotImplementedError
        # request = requests.post(f"/_apis/teams?api-version=7.1", json={"name": name, "description": description}, auth=ado_client.auth).json()
        # return cls.from_request_payload(request)

    def update(self, ado_client: AdoClient, attribute_name: str, attribute_value: str) -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, team_id: str) -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["Team"]:  # type: ignore[override]
        return super().get_all(
            ado_client,
            "/_apis/teams?api-version=7.1-preview.2",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, team_name: str) -> "Team":
        for team in cls.get_all(ado_client):
            if team.name == team_name:
                return team
        raise ValueError(f"Team {team_name} not found")

    def get_members(self, ado_client: AdoClient) -> list["TeamMember"]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/_apis/projects/{ado_client.ado_project}/teams/{self.team_id}/members?api-version=7.1-preview.2",
            auth=ado_client.auth,
        ).json()
        if "value" not in request and request.get("message", "").startswith("The team with id "):  # If the team doesn't exist anymore.
            return []
        team_members = [TeamMember.from_request_payload(member) for member in request["value"]]
        self.team_members = team_members
        return team_members

    def delete(self, ado_client: AdoClient, team_id: str) -> None:
        self.delete_by_id(ado_client, team_id)

    # @staticmethod
    # def _recursively_extract_teams(ado_client: AdoClient, team_or_member: Team | TeamMember):
    #     if isinstance(team_or_member, Team):
    #         rint("Found a team!")
    #         team_or_member.get_members(ado_client)
    #         for member in team_or_member.team_members:
    #             Team._recursively_extract_teams(ado_client, member)
    #     return team_or_member

    # @classmethod
    # def get_all_teams_recursively(cls, ado_client: AdoClient) -> list["TeamMember | Team"]:
    #     all_teams = [
    #         cls._recursively_extract_teams(ado_client, team)
    #         for team in cls.get_all(ado_client)
    #     ]
    #     return all_teams  # type: ignore[return-value]

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

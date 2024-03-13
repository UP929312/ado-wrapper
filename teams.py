from __future__ import annotations

from typing import TYPE_CHECKING

import requests

from users import TeamMember

if TYPE_CHECKING:
    from client import AdoClient


class Team:
    """Describe a Azure DevOps team"""

    def __init__(self, team_id: str, name: str, description: str) -> None:
        self.team_id = team_id
        self.name = name
        self.description = description

    def __str__(self) -> str:
        return f"{self.name} ({self.team_id})"

    def __repr__(self) -> str:
        return f"Team({self.team_id!r}, {self.name!r}, {self.description!r})"

    def to_json(self) -> dict[str, str]:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
        }

    @classmethod
    def from_json(cls, data: dict[str, str]) -> "Team":
        return cls(data["team_id"], data["name"], data["description"])

    @classmethod
    def from_request_payload(cls, team_response: dict[str, str]) -> "Team":
        return cls(team_response["id"], team_response["name"], team_response.get("description", ""))

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, team_id: str) -> "Team":
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/_apis/projects/{ado_client.ado_project}/teams/{team_id}?$expandIdentity={True}&api-version=7.1-preview.2",
            auth=ado_client.auth,
        ).json()
        return cls.from_request_payload(request)

    @classmethod
    def create(cls, ado_client: AdoClient, name: str, description: str) -> "Team":
        raise NotImplementedError
        # request = requests.post(f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/teams?api-version=7.1-preview.2", json={"name": name, "description": description}, auth=ado_client.auth).json()
        # return cls.from_request_payload(request)

    @classmethod
    def delete(cls, ado_client: AdoClient, team_id: str) -> None:
        raise NotImplementedError
        # request = requests.delete(f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/teams/{team_id}?api-version=7.1-preview.2", auth=ado_client.auth)
        # assert request.status_code < 300

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["Team"]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/_apis/projects/{ado_client.ado_project}/teams?api-version=7.1-preview.2",
            auth=ado_client.auth,
        ).json()["value"]
        return [cls.from_request_payload(team) for team in request]

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
        ).json()["value"]
        return [TeamMember.from_request_payload(member) for member in request]

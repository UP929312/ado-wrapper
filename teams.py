from __future__ import annotations

from typing import TYPE_CHECKING

# import requests

if TYPE_CHECKING:
    from client import AdoClient


class Team:
    def __init__(self, team_id: str, name: str, description: str) -> None:
        self.team_id = team_id
        self.name = name
        self.description = description

    def __str__(self) -> str:
        return f"{self.name} ({self.team_id})"

    def __repr__(self) -> str:
        return f"Team({self.team_id!r}, {self.name!r}, {self.description!r})"

    @classmethod
    def from_json(cls, team_response: dict[str, str]) -> "Team":
        return cls(team_response["id"], team_response["name"], team_response.get("description", ""))

    # @classmethod
    # def create(cls, ado_client: AdoHelper, name: str, description: str) -> "Team":
    #     request = requests.post(f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/teams?api-version=7.1-preview.2", json={"name": name, "description": description}, auth=ado_client.auth).json()
    #     return cls.from_json(request)

    # @classmethod  # We don't have vssps (identity) access, so we can't use this
    # def get_all_teams(cls, ado_client: AdoHelper) -> list["Team"]:
    #     request = requests.get(f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/teams?api-version=7.1-preview.2", auth=ado_client.auth).json()
    #     return [cls.from_json(team) for team in request["value"]]

    # @classmethod  # We don't have vssps (identity) access, so we can't use this
    # def get_team_by_id(cls, ado_client: AdoHelper, team_id: str) -> "Team":
    #     request = requests.get(f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/teams/{team_id}?api-version=7.1-preview.2", auth=ado_client.auth).json()
    #     return cls.from_json(request)

    # @classmethod  # We don't have vssps (identity) access, so we can't use this
    # def get_team_by_name(cls, ado_client: AdoHelper, team_name: str) -> "Team":
    #     request = requests.get(f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/teams?api-version=7.1-preview.2", auth=ado_client.auth).json()
    #     for team in request["value"]:
    #         if team["name"] == team_name:
    #             return cls.from_json(team)
    #     raise ValueError(f"Team {team_name} not found")

    # @classmethod
    # def delete(cls, ado_client: AdoHelper, team_id: str) -> None:
    #     request = requests.delete(f"https://vssps.dev.azure.com/{ado_client.ado_org}/_apis/teams/{team_id}?api-version=7.1-preview.2", auth=ado_client.auth)
    #     assert request.status_code < 300


if __name__ == "__main__":
    from secret import email, ado_access_token, ado_org, ado_project
    from client import AdoClient

    ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass, field

import requests

from state_managed_abc import StateManagedResource
from resources.users import TeamMember

if TYPE_CHECKING:
    from client import AdoClient


@dataclass
class Team(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/core/teams?view=azure-devops-rest-7.1"""

    team_id: str = field(metadata={"is_id_field": True}) # None are editable
    name: str
    description: str

    def __str__(self) -> str:
        return f"{self.name} ({self.team_id})"

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
    def create(cls, ado_client: AdoClient, name: str, description: str) -> "Team":  # type: ignore[override]
        raise NotImplementedError
        # request = requests.post(f"https://dev.azure.com/{ado_client.ado_org}/_apis/teams?api-version=7.1-preview.2", json={"name": name, "description": description}, auth=ado_client.auth).json()
        # return cls.from_request_payload(request)

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, team_id: str) -> None:  # type: ignore[override]
        raise NotImplementedError
        # request = requests.delete(f"https://dev.azure.com/{ado_client.ado_org}/_apis/teams/{team_id}?api-version=7.1-preview.2", auth=ado_client.auth)
        # assert request.status_code < 300

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["Team"]:  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/_apis/projects/{ado_client.ado_project}/teams?api-version=7.1-preview.2",
        )  # type: ignore[return-value]

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

    def delete(self, ado_client: AdoClient, team_id: str) -> None:
        self.delete_by_id(ado_client, team_id)

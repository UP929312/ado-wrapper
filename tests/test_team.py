import pytest

from ado_wrapper.resources.teams import Team
from ado_wrapper.resources.users import TeamMember
from tests.setup_client import setup_client, existing_team_name, existing_team_id


class TestTeam:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        team = Team.from_request_payload({"id": "123", "name": "test-Team", "description": "test-Team"})
        assert isinstance(team, Team)
        assert team.team_id == "123"
        assert team.name == "test-Team"
        assert team.description == "test-Team"
        assert team.to_json() == Team.from_json(team.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_team(self) -> None:
        with pytest.raises(NotImplementedError):
            Team.create(self.ado_client, "ado_wrapper-test-Team", "description")
        with pytest.raises(NotImplementedError):
            Team.delete_by_id(self.ado_client, "abc")

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        team = Team.get_by_id(self.ado_client, existing_team_id)
        assert team.team_id == existing_team_id

    def test_get_all(self) -> None:
        teams = Team.get_all(self.ado_client)
        assert len(teams) > 1
        assert all(isinstance(team, Team) for team in teams)

    def test_get_by_name(self) -> None:
        team = Team.get_by_name(self.ado_client, existing_team_name)
        assert team is not None
        assert team.name == existing_team_name

    def test_get_members(self) -> None:
        team = Team.get_by_name(self.ado_client, existing_team_name)
        assert team is not None
        members = team.get_members(self.ado_client)
        assert len(members) > 1
        assert all(isinstance(member, TeamMember) for member in members)

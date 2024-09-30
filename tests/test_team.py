import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.teams import Team
from ado_wrapper.resources.users import TeamMember
from tests.setup_client import setup_client


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
        team = Team.create(self.ado_client, "ado_wrapper-test-Team", "description")
        team.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        team_created = Team.create(self.ado_client, "ado_wrapper-test-get-by-id-team", "description")
        team = Team.get_by_id(self.ado_client, team_created.team_id)
        assert team.team_id == team_created.team_id
        team_created.delete(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        team_created = Team.create(self.ado_client, "ado_wrapper-test-get-all-teams", "description")
        teams = Team.get_all(self.ado_client)
        assert len(teams) >= 1
        assert all(isinstance(team, Team) for team in teams)
        team_created.delete(self.ado_client)

    @pytest.mark.get_all_by_name
    def test_get_by_name(self) -> None:
        team_created = Team.create(self.ado_client, "ado_wrapper-test-get-all-by-name", "description")
        team = Team.get_by_name(self.ado_client, team_created.name)
        assert team is not None
        assert team.name == team_created.name
        team_created.delete(self.ado_client)

    @pytest.mark.skip("Need to come back to this!")  # TODO: Adding people to teams
    def test_get_members(self) -> None:
        team_created = Team.create(self.ado_client, "ado_wrapper-test-get-members", "description")
        team = Team.get_by_name(self.ado_client, team_created.name)
        assert team is not None
        members = team.get_members(self.ado_client)
        assert len(members) > 1
        assert all(isinstance(member, TeamMember) for member in members)
        team_created.delete(self.ado_client)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

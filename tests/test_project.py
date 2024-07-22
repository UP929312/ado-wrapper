import pytest

from ado_wrapper.resources.projects import Project
from tests.setup_client import existing_project_id, existing_project_name, setup_client


class TestProject:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        project = Project.from_request_payload(
            {
                "id": "123",
                "name": "test-project",
                "description": "test-description",
            }
        )
        assert isinstance(project, Project)
        assert project.project_id == "123"
        assert project.name == "test-project"
        assert project.description == "test-description"
        assert project.to_json() == Project.from_json(project.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_project(self) -> None:
        with pytest.raises(NotImplementedError):
            Project.create(self.ado_client, "ado_wrapper-test-project", "description")

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        project = Project.get_by_id(self.ado_client, existing_project_id)
        assert project.project_id == existing_project_id

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        projects = Project.get_all(self.ado_client)
        assert len(projects) >= 1
        assert all(isinstance(project, Project) for project in projects)

    @pytest.mark.get_all_by_name
    def test_get_by_name(self) -> None:
        project = Project.get_by_name(self.ado_client, existing_project_name)
        assert project is not None
        assert project.name == existing_project_name

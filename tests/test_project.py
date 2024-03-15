from client import AdoClient
from resources.projects import Project

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    (
        ado_org, ado_project, email, pat_token, _, _, _, _, _, _,
        existing_project_name, existing_project_id, *_,  # fmt: skip
    ) = test_data.read().splitlines()  # type: ignore[assignment]


class TestProject:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

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

    def test_get_by_id(self) -> None:
        project = Project.get_by_id(self.ado_client, existing_project_id)
        assert project.project_id == existing_project_id

    def test_get_all(self) -> None:
        projects = Project.get_all(self.ado_client)
        assert len(projects) >= 1
        assert all(isinstance(project, Project) for project in projects)

    def test_get_by_name(self) -> None:
        project = Project.get_by_name(self.ado_client, existing_project_name)
        assert project is not None
        assert project.name == existing_project_name

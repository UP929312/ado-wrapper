import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

# from ado_wrapper.resources.projects import Project
# from ado_wrapper.resources.project_settings import (
#    ProjectOverviewSettings, ProjectBuildQueueSettings, ProjectPipelineSettings, ProjectRepositoryPolicies, ProjectRepositorySettings, ProjectTestRetentionSettings
# )
from ado_wrapper.resources.project_settings import ProjectRepositoryPolicySettings, ProjectRepositorySettings
from tests.setup_client import setup_client


class TestProjectSettings:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        # =================================================================
        repo_policy = ProjectRepositoryPolicySettings.from_request_payload(
            {
                "id": "123",
                "isEnabled": True,
                "type": {"displayName": "File name restriction"},
                "settings": {"filenamePatterns": True},
            }
        )
        assert isinstance(repo_policy, ProjectRepositoryPolicySettings)
        assert repo_policy.policy_id == "123"
        assert repo_policy.enabled
        assert repo_policy.programmatic_name == "file_path_validation"
        assert repo_policy.display_name == "File name restriction"
        # =================================================================
        DESCRIPTION = "New repositories will be initialized with this branch. You can change the default branch for a particular repository at any time."
        repo_settings = ProjectRepositorySettings.from_request_payload(
            {
                "key": "DefaultBranchName",
                "title": "Default branch name for new repositories",
                "displayHtml": DESCRIPTION,
                "value": True,
                "isDisabled": False,
                "textValue": "new-default-branch-name",
                "defaultTextValue": "main",
            }
        )
        assert isinstance(repo_settings, ProjectRepositorySettings)
        assert repo_settings.programmatic_name == "default_branch_name"
        assert repo_settings.internal_name == "DefaultBranchName"
        assert repo_settings.title == "Default branch name for new repositories"
        assert repo_settings.description == DESCRIPTION
        assert repo_settings.setting_enabled
        assert not repo_settings.disabled_by_inheritence
        assert repo_settings.override_string_value == "new-default-branch-name"
        assert repo_settings.default_value == "main"

    # @pytest.mark.skip("This requires initialisation, which can take 5 minutes.")
    # @pytest.mark.create_delete
    # def test_create_delete_project(self) -> None:
    #     project = Project.create(self.ado_client, "ado_wrapper-test-project-3", "description", "Agile")
    #     project.delete(self.ado_client)

    # @pytest.mark.skip("This requires initialisation, which can take 5 minutes.")
    # @pytest.mark.get_by_id
    # def test_get_by_id(self) -> None:
    #     project_created = Project.create(self.ado_client, "ado_wrapper-test-project-get-by-id", "description", "Agile")
    #     time.sleep(60 * 5)  # Wait 5 minutes
    #     project = Project.get_by_id(self.ado_client, project_created.project_id)  # It takes a few minutes for a project to be ready
    #     assert project.project_id == project_created.project_id
    #     project_created.delete(self.ado_client)

    # @pytest.mark.skip("This requires initialisation, which can take 5 minutes.")
    # @pytest.mark.get_all
    # def test_get_all(self) -> None:
    #     project_created = Project.create(self.ado_client, "ado_wrapper-test-project-get-all", "description", "Agile")
    #     time.sleep(60 * 5)  # Wait 5 minutes
    #     projects = Project.get_all(self.ado_client)
    #     print(projects)
    #     assert len(projects) >= 1
    #     assert all(isinstance(project, Project) for project in projects)
    #     project_created.delete(self.ado_client)

    # @pytest.mark.skip("This requires initialisation, which can take 5 minutes.")
    # @pytest.mark.get_all_by_name
    # def test_get_by_name(self) -> None:
    #     project_created = Project.create(self.ado_client, "ado_wrapper-test-project-get-by-name", "description", "Agile")
    #     time.sleep(60 * 5)  # Wait 5 minutes
    #     project = Project.get_by_name(self.ado_client, project_created.name)
    #     assert project is not None
    #     assert project.name == project_created.name
    #     project_created.delete(self.ado_client)

    # @pytest.mark.skip("This requires initialisation, which can take 5 minutes.")
    # @pytest.mark.get_all_by_name
    # def test_project_settings(self) -> None:
    #     # TODO: Maybe try setting them as well?
    #     project_created = Project.create(self.ado_client, "ado_wrapper-test_project_settings", "description", "Agile")
    #     time.sleep(60 * 10)  # Wait 10 minutes
    #     settings = ProjectRepositorySettings.get_by_project(self.ado_client, project_created.name)
    #     assert not settings["default_branch_name"].setting_enabled
    #     assert not settings["pull_request_as_draft_by_default"].setting_enabled
    #     project_created.delete(self.ado_client)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vvvv"])
    # pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

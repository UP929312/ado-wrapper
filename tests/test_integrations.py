import pytest

from client import AdoClient
from resources.variable_groups import VariableGroup
from resources.repo import Repo
from resources.commits import Commit
from resources.builds import Build, BuildDefinition


with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    (
        ado_org, ado_project, email, pat_token, _, _, _, _, _, existing_agent_pool_id, *_  # fmt: skip
    ) = test_data.read().splitlines()  # type: ignore[assignment]

BUILD_YAML_FILE = """---
trigger:
  - main

pool:
  vmImage: ubuntu-latest

variables:
  - group: ado-api-test-for-integrations

steps:
  - script: echo Hello, world!
    displayName: 'Integrations Testing'"""


class TestIntegrations:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project, state_file_name="tests/test_state.state")

    @pytest.mark.integrations
    @pytest.mark.skip("This test is not meant to be run in CI/CD, just manually")
    def test_through(self) -> None:
        # Creates a variable group, repo, build definition (which prints out the variable group value),
        # then runs the build, waits for it to complete, then clears up
        BRANCH_NAME = "testing-branch"
        variable_group = VariableGroup.create(self.ado_client, "ado-api-test-for-integrations", "my_description", {"a": "b"})
        repo = Repo.create(self.ado_client, "ado-api-test-for-integrations-repo")
        Commit.create(self.ado_client, repo.repo_id, "main", BRANCH_NAME, {"build.yaml": BUILD_YAML_FILE}, "add", "Initial commit")
        build_definition = BuildDefinition.create(self.ado_client, "ado-api-test-for-integrations-build-definition", repo.repo_id, repo.name,
                                                  "build.yaml", "Desc", existing_agent_pool_id, [variable_group.variable_group_id], BRANCH_NAME)  # fmt: skip
        build = Build.create_and_wait_until_completion(self.ado_client, build_definition.build_definition_id, BRANCH_NAME)
        assert build.status == "completed"
        variable_group.delete(self.ado_client)
        build_definition.delete(self.ado_client)
        repo.delete(self.ado_client)

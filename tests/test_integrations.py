import pytest

from ado_wrapper.resources.build_definitions import BuildDefinition
from ado_wrapper.resources.builds import Build
from ado_wrapper.resources.commits import Commit
from ado_wrapper.resources.repo import Repo

# from ado_wrapper.resources.variable_groups import VariableGroup

from tests.setup_client import existing_agent_pool_id, setup_client

BUILD_YAML_FILE = """---
trigger:
  - main

pool:
  vmImage: ubuntu-latest

variables:
  - group: ado_wrapper-test-for-integrations

steps:
  - script: echo Hello, world!
    displayName: 'Integrations Testing'"""


class TestIntegrations:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.integrations
    @pytest.mark.skip("This test is not meant to be run in CI/CD, just manually")
    def test_through(self) -> None:
        # Creates a variable group, repo, build definition (which outputs out the variable group value),
        # then runs the build, waits for it to complete, then clears up
        BRANCH_NAME = "testing-branch"
        # variable_group = VariableGroup.create(self.ado_client, "ado_wrapper-test-for-integrations", "my_description", {"a": "b"})
        repo = Repo.create(self.ado_client, "ado_wrapper-test-for-integrations-repo")
        Commit.create(self.ado_client, repo.repo_id, "main", BRANCH_NAME, {"build.yaml": BUILD_YAML_FILE}, "add", "Initial commit")
        build_definition = BuildDefinition.create(self.ado_client, "ado_wrapper-test-for-integrations-build-definition", repo.repo_id, repo.name,
                                                  "build.yaml", "Desc", existing_agent_pool_id, BRANCH_NAME)  # fmt: skip
        build = Build.create_and_wait_until_completion(self.ado_client, build_definition.build_definition_id, BRANCH_NAME)
        assert build.status == "completed"
        # variable_group.delete(self.ado_client)
        build_definition.delete(self.ado_client)
        repo.delete(self.ado_client)

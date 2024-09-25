from datetime import datetime

import pytest

from ado_wrapper.resources.build_definitions import BuildDefinition
from ado_wrapper.resources.commits import Commit
from ado_wrapper.resources.environment import Environment
from ado_wrapper.resources.users import Member
from tests.setup_client import RepoContextManager, setup_client
from tests.build_definition_templates import MOST_BASIC_BUILD_YAML_FILE


class TestEnvironment:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        environment = Environment.create(self.ado_client, "ado_wrapper-test-environment", "test environment")
        assert environment is not None
        assert environment.name == "ado_wrapper-test-environment"
        assert environment.description == "test environment"
        assert isinstance(environment.created_by, Member)
        assert isinstance(environment.created_on, datetime)
        assert environment.modified_by is None
        assert environment.modified_on is None
        # ---
        environment.delete(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        environment = Environment.create(self.ado_client, "ado_wrapper-test-environment-update", "test environment")
        # ---
        environment.update(self.ado_client, "description", "updated description")
        assert environment.name == "ado_wrapper-test-environment-update"
        assert environment.description == "updated description"
        # ---
        updated_env = environment.get_by_id(self.ado_client, environment.environment_id)
        assert updated_env.name == "ado_wrapper-test-environment-update"
        assert updated_env.description == "updated description"
        # ---
        environment.update(self.ado_client, "name", "ado_wrapper-test-environment-renamed")
        assert environment.name == "ado_wrapper-test-environment-renamed"
        assert environment.description == "updated description"
        # ---
        updated_again_env = environment.get_by_id(self.ado_client, environment.environment_id)
        assert updated_again_env.name == "ado_wrapper-test-environment-renamed"
        assert updated_again_env.description == "updated description"
        # ---
        environment.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        environment = Environment.create(self.ado_client, "ado_wrapper-test-environment-get-by-id", "test environment")
        # ---
        fetched_environment = Environment.get_by_id(self.ado_client, environment.environment_id)
        assert fetched_environment.name == "ado_wrapper-test-environment-get-by-id"
        assert fetched_environment.description == "test environment"
        # ---
        environment.delete(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        environment = Environment.create(self.ado_client, "ado_wrapper-test-get-all", "Test")
        environments = Environment.get_all(self.ado_client)
        assert len(environments) >= 1
        assert all(isinstance(env, Environment) for env in environments)
        environment.delete(self.ado_client)

    @pytest.mark.get_all_by_name
    def test_get_by_name(self) -> None:
        environment = Environment.create(self.ado_client, "ado_wrapper-test-environment-get-by-name", "test environment")
        # ---
        fetched_environment: Environment = Environment.get_by_name(self.ado_client, "ado_wrapper-test-environment-get-by-name")  # type: ignore[assignment]
        assert fetched_environment.name == "ado_wrapper-test-environment-get-by-name"
        assert fetched_environment.description == "test environment"
        # ---
        environment.delete(self.ado_client)

    def test_pipeline_perms(self) -> None:
        with RepoContextManager(self.ado_client, "pipeline_perms") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "test commit")
            build_def = BuildDefinition.create(
                self.ado_client, repo.name, repo.repo_id, repo.name, "build.yaml", "", branch_name="my-branch"
            )  # fmt: skip

        environment = Environment.create(self.ado_client, "ado_wrapper-test-environment-pipeline-perms", "test environment")
        # ---
        perms = environment.get_pipeline_permissions(self.ado_client)
        assert perms is not None
        environment.add_pipeline_permission(self.ado_client, build_def.build_definition_id)
        new_perms = environment.get_pipeline_permissions(self.ado_client)
        assert len(new_perms) == 1
        environment.remove_pipeline_permissions(self.ado_client, build_def.build_definition_id)
        final_perms = environment.get_pipeline_permissions(self.ado_client)
        assert len(final_perms) == 0
        # ---
        build_def.delete(self.ado_client)
        environment.delete(self.ado_client)

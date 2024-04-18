from datetime import datetime
import pytest

from ado_wrapper.resources.environment import Environment
from ado_wrapper.resources.users import Member

from tests.setup_client import setup_client


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
        environments = Environment.get_all(self.ado_client)
        assert len(environments) > 1
        assert all(isinstance(env, Environment) for env in environments)

    @pytest.mark.get_all_by_name
    def test_get_by_name(self) -> None:
        environment = Environment.create(self.ado_client, "ado_wrapper-test-environment-get-by-name", "test environment")
        # ---
        fetched_environment = Environment.get_by_name(self.ado_client, "ado_wrapper-test-environment-get-by-name")
        assert fetched_environment.name == "ado_wrapper-test-environment-get-by-name"
        assert fetched_environment.description == "test environment"
        # ---
        environment.delete(self.ado_client)

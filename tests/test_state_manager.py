import pytest

if __name__ == "__main__":
    __import__('sys').path.insert(0, __import__('os').path.abspath(__import__('os').path.dirname(__file__) + '/..'))

# from ado_wrapper.resources.variable_groups import VariableGroup
# from ado_wrapper.resources.service_endpoint import ServiceEndpoint
from tests.setup_client import RepoContextManager, setup_client


class TestStateManager:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    def test_load_all_resources_with_prefix(self) -> None:
        state_manager = self.ado_client.state_manager

        with RepoContextManager(self.ado_client, "test_load_all_resources_with_prefix") as repo:
            state_manager.remove_resource_from_state("Repo", repo.repo_id)
            # variable_group = VariableGroup.create(self.ado_client, "ado_wrapper-test_load_all_resources_with_prefix", "test", {"a": "123"})
            # service_endpoint = ServiceEndpoint.create(self.ado_client, "ado_wrapper-test_load_all_resources_with_prefix",
            #                                           "github", "https://github.com", "username", "password")  # fmt: skip
            state_manager.load_all_resources_with_prefix_into_state("ado_wrapper-")
            all_states = state_manager.load_state()["resources"]
            assert all_states["Repo"][repo.repo_id]["data"] == repo.to_json()
            # assert all_states["VariableGroup"][variable_group.variable_group_id]["data"] == variable_group.to_json()
            # assert all_states["ServiceEndpoint"][service_endpoint.service_endpoint_id]["data"] == service_endpoint.to_json()
            # variable_group.delete(self.ado_client)
            # service_endpoint.delete(self.ado_client)

    def test_generate_in_memory_state(self) -> None:
        state_manager = self.ado_client.state_manager

        with RepoContextManager(self.ado_client, "test_generate_in_memory_state") as repo:
            state_manager.generate_in_memory_state()
            assert state_manager.load_state()["resources"]["Repo"][repo.repo_id]["data"] == repo.to_json()

    def test_import_into_state(self) -> None:
        state_manager = self.ado_client.state_manager

        with RepoContextManager(self.ado_client, "test_import_into_state") as repo:
            state_manager.remove_resource_from_state("Repo", repo.repo_id)
            state_manager.import_into_state("Repo", repo.repo_id)
            assert state_manager.load_state()["resources"]["Repo"][repo.repo_id]["data"] == repo.to_json()


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

import os

from ado_wrapper.client import AdoClient
from ado_wrapper.resources.repo import Repo

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()


class TestState:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project, state_file_name="tests/test_actual_state.state")

    def test_adding_deleting(self) -> None:
        fake_repo = Repo("123", "test-repo", "master", False)
        self.ado_client.state_manager.add_resource_to_state("Repo", fake_repo.repo_id, fake_repo.to_json())
        assert self.ado_client.state_manager.load_state()["resources"]["Repo"]["123"]["data"] == fake_repo.to_json()
        self.ado_client.state_manager.remove_resource_from_state("Repo", fake_repo.repo_id)
        assert self.ado_client.state_manager.load_state()["resources"]["Repo"] == {}

        self.ado_client.state_manager.add_resource_to_state("Repo", fake_repo.repo_id, fake_repo.to_json())
        self.ado_client.state_manager.wipe_state()
        assert self.ado_client.state_manager.load_state()["resources"]["Repo"] == {}

        self.ado_client.state_manager.add_resource_to_state("Repo", fake_repo.repo_id, fake_repo.to_json())
        self.ado_client.state_manager.update_resource_in_state("Repo", fake_repo.repo_id, fake_repo.to_json() | {"name": "new-name"})
        assert self.ado_client.state_manager.load_state()["resources"]["Repo"]["123"]["data"] == fake_repo.to_json() | {"name": "new-name"}

    def test_zz_cleanup(self) -> None:
        os.remove("tests/test_actual_state.state")

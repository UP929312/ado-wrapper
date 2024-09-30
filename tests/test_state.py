import os

import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.client import AdoClient
from ado_wrapper.resources.repo import Repo
from tests.setup_client import ado_org_name, ado_project, email, pat_token


class TestState:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org_name, ado_project, state_file_name="tests/test_actual_state.state")

    def test_adding_deleting(self) -> None:
        state_manager = self.ado_client.state_manager

        fake_repo = Repo("123", "test-repo", "master", False)
        state_manager.add_resource_to_state("Repo", fake_repo.repo_id, fake_repo.to_json())
        assert state_manager.load_state()["resources"]["Repo"]["123"]["data"] == fake_repo.to_json()
        state_manager.remove_resource_from_state("Repo", fake_repo.repo_id)
        assert state_manager.load_state()["resources"]["Repo"] == {}

        state_manager.add_resource_to_state("Repo", fake_repo.repo_id, fake_repo.to_json())
        state_manager.wipe_state()
        assert state_manager.load_state()["resources"]["Repo"] == {}

        state_manager.add_resource_to_state("Repo", fake_repo.repo_id, fake_repo.to_json())
        state_manager.update_resource_in_state("Repo", fake_repo.repo_id, fake_repo.to_json() | {"name": "new-name"})
        assert state_manager.load_state()["resources"]["Repo"]["123"]["data"] == fake_repo.to_json() | {"name": "new-name"}

    def test_zz_cleanup(self) -> None:
        os.remove("tests/test_actual_state.state")


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.projects import Project
from ado_wrapper.errors import NoElevatedPrivilegesError

from tests.setup_client import setup_client, ado_project_name, secondary_project_name


class TestStateManager:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    def test_temporary_polling_interval(self) -> None:
        assert self.ado_client.run_polling_interval_seconds == 30
        with self.ado_client.temporary_polling_interval(5):
            assert self.ado_client.run_polling_interval_seconds == 5
        assert self.ado_client.run_polling_interval_seconds == 30

    def test_elevated_privileges(self) -> None:
        assert not self.ado_client.has_elevate_privileges
        with self.ado_client.elevated_privileges():
            assert self.ado_client.has_elevate_privileges
        assert not self.ado_client.has_elevate_privileges

    def test_elevated_privileges_actual(self) -> None:
        self.ado_client.has_elevate_privileges = False
        with pytest.raises(NoElevatedPrivilegesError):
            Project.create(self.ado_client, "abc", "abc", "Agile")

    def test_assume_role(self) -> None:
        assert self.ado_client.ado_project_name == ado_project_name
        self.ado_client.assume_project(secondary_project_name)
        assert self.ado_client.ado_project_name == secondary_project_name
        self.ado_client.assume_project(ado_project_name)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vvvv"])
    # pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

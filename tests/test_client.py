import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))


from tests.setup_client import setup_client


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


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vvvv"])
    # pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])

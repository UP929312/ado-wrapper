from tests.setup_client import setup_client


class TestZZCleanup:
    """The purpose of this is to cleanup old resources if any tests fail"""

    def test_zz_cleanup(self) -> None:
        ado_client = setup_client()
        ado_client.state_manager.delete_all_resources()

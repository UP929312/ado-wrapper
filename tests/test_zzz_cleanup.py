from client import AdoClient

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()


class TestZZZCleanup:
    """The purpose of this is to cleanup old resources if any tests fail"""
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project, state_file_name="tests/test_state.state")

    def cleanup(self) -> None:
        self.ado_client.state_manager.delete_all_resources()

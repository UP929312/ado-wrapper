from ado_wrapper.client import AdoClient

with open("tests/test_data.txt", encoding="utf-8") as test_data:
    ado_org_name, ado_project_name, secondary_project_name, email, pat_token, existing_user_id, existing_user_descriptor = test_data.read().splitlines()  # fmt: skip
existing_user_name = email.split("@")[0].replace(".", " ").title().split(".")[0]

ado_client = AdoClient(email, pat_token, ado_org_name, ado_project_name, "tests/test_state.state")

REPO_PREFIX = "ado_wrapper-test-repo-for-"


def setup_client() -> AdoClient:
    return ado_client

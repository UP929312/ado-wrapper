import os

from ado_wrapper.client import AdoClient

if not os.path.exists("tests/test_data.txt"):
    raise FileNotFoundError(
        "The test_data.txt file is missing. Please create it with the required test data!\n"
        "The file should contain the following lines:\n"
        "1. Azure DevOps organisation name\n"
        "2. Azure DevOps project name\n"
        "3. Secondary project name (for testing purposes, can normally be an empty line)\n"
        "4. Email address for the Azure DevOps account\n"
        "5. Personal Access Token (PAT) for the Azure DevOps account\n"
        "6. Existing user ID, also retrievable through print(AdoUser.get_by_email(ado_client, 'first.last@company.com').origin_id)\n",
        "7. Existing user descriptor, also retrievable through print(AdoUser.get_by_email(ado_client, 'first.last@company.com').descriptor_id)\n"
    )

with open("tests/test_data.txt", encoding="utf-8") as test_data:
    ado_org_name, ado_project_name, secondary_project_name, email, pat_token, existing_user_id, existing_user_descriptor = test_data.read().splitlines()  # fmt: skip
existing_user_name = email.split("@")[0].replace(".", " ").title().split(".")[0]

ado_client = AdoClient(email, pat_token, ado_org_name, ado_project_name, "tests/test_state.state",
                       latest_log_count=3, log_directory="tests/ado_wrapper_logs")  # fmt: skip

REPO_PREFIX = "ado_wrapper-test-repo-for-"


def setup_client() -> AdoClient:
    return ado_client

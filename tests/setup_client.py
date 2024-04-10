from ado_wrapper.client import AdoClient

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    (
        ado_org, ado_project, email, pat_token, existing_team_name, existing_team_id, existing_user_name,
        existing_user_email, existing_user_id, existing_agent_pool_id, existing_project_name, existing_project_id, 
        existing_group_descriptor, existing_group_name
    )= test_data.read().splitlines()

ado_client = AdoClient(email, pat_token, ado_org, ado_project, "tests/test_state.state", bypass_initialisation=False)

def setup_client():
    return ado_client
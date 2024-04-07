import requests
from requests.auth import HTTPBasicAuth

from ado_wrapper.state_manager import StateManager
from ado_wrapper.utils import AuthenticationError


class AdoClient:
    def __init__(  # pylint: disable=too-many-arguments
        self, ado_email: str, ado_pat: str, ado_org: str, ado_project: str,
        state_file_name: str | None = "main.state", bypass_initialisation: bool = False # fmt: skip
    ) -> None:
        """Takes an email, PAT, org, project, and state file name. The state file name is optional, and if not provided,
        state will not be stored in "main.state" """
        self.ado_email = ado_email
        self.ado_pat = ado_pat
        self.auth = HTTPBasicAuth(ado_email, ado_pat)
        self.ado_org = ado_org
        self.ado_project = ado_project
        self.plan = False

        if not bypass_initialisation:
            # Verify Token is working (helps with setup for first time users):
            request = requests.get(f"https://dev.azure.com/{self.ado_org}/_apis/projects?api-version=7.1", auth=self.auth)
            if request.status_code != 200:
                raise AuthenticationError(f"Failed to authenticate with ADO: {request.text}")

            from ado_wrapper.resources.projects import Project  # Stop circular import
            self.ado_project_id = Project.get_by_name(self, self.ado_project).project_id  # type: ignore[union-attr]

            from ado_wrapper.resources.users import AdoUser  # Stop circular import
            try:
                self.pat_author: AdoUser = AdoUser.get_by_email(self, ado_email)
            except ValueError:
                print(f"[ADO_WRAPPER] WARNING: User {ado_email} not found in ADO, nothing critical, but stops releases from being made, and plans from being accurate.")

        self.state_manager: StateManager = StateManager(self, state_file_name)  # Has to be last

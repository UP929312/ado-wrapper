from typing import Literal

import requests
from requests.auth import HTTPBasicAuth

from ado_wrapper.plan_resources.plan_state_manager import PlanStateManager
from ado_wrapper.state_manager import StateManager
from ado_wrapper.errors import AuthenticationError


class AdoClient:
    def __init__(  # pylint: disable=too-many-arguments
        self, ado_email: str, ado_pat: str, ado_org: str, ado_project: str,
        state_file_name: str | None = "main.state", suppress_warnings: bool = False,
        bypass_initialisation: bool = False, action: Literal["plan", "apply"] = "apply"  # fmt: skip
    ) -> None:
        """Takes an email, PAT, org, project, and state file name. The state file name is optional, and if not provided,
        state will be stored in "main.state" (can be disabled using None)"""
        self.ado_email = ado_email
        self.ado_pat = ado_pat
        self.ado_org = ado_org
        self.ado_project = ado_project

        self.suppress_warnings = suppress_warnings
        self.plan_mode = action == "plan"

        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(ado_email, ado_pat)

        if not bypass_initialisation:
            # Verify Token is working (helps with setup for first time users):
            request = self.session.get(f"https://dev.azure.com/{self.ado_org}/_apis/projects?api-version=7.1")
            if request.status_code != 200:
                raise AuthenticationError("Failed to authenticate with ADO: Most likely incorrect token or expired token!")

            from ado_wrapper.resources.projects import Project  # Stop circular import
            from ado_wrapper.resources.users import AdoUser  # Stop circular import

            self.ado_project_id = Project.get_by_name(self, self.ado_project).project_id  # type: ignore[union-attr]
            try:
                self.pat_author: AdoUser = AdoUser.get_by_email(self, ado_email)
            except ValueError:
                if not suppress_warnings:
                    print(
                        f"[ADO_WRAPPER] WARNING: User {ado_email} not found in ADO, nothing critical, but stops releases from being made, and plans from being accurate."
                    )

        self.state_manager = StateManager(self, state_file_name) if action == "apply" else PlanStateManager(self)  # Has to be last

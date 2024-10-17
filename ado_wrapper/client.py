from contextlib import contextmanager
from typing import Generator

import requests
from requests.auth import HTTPBasicAuth

from ado_wrapper.state_manager import StateManager
from ado_wrapper.errors import AuthenticationError, InvalidPermissionsError


class AdoClient:
    def __init__(  # pylint: disable=too-many-arguments
        self, ado_email: str, ado_pat: str, ado_org_name: str, ado_project_name: str,
        state_file_name: str | None = "main.state", suppress_warnings: bool = False,
        run_polling_interval_seconds: int = 30, bypass_initialisation: bool = False,  # fmt: skip
    ) -> None:
        """Takes an email, PAT, org, project, and state file name. The state file name is optional, and if not provided,
        state will be stored in "main.state" (can be disabled using `None`)\n
        Run polling interval is how often a run will be checked when using run_and_wait_until_complete and it's sibling functions.\n
        Bypass initialisation means the client won't fetch certain info on startup and therefor some functions won't work."""

        self.ado_email = ado_email
        self.ado_pat = ado_pat
        self.ado_org_name = ado_org_name
        self.ado_project_name = ado_project_name
        # self.perms = None

        self.suppress_warnings = suppress_warnings
        self.run_polling_interval_seconds = run_polling_interval_seconds
        self.has_elevate_privileges = False

        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(ado_email, ado_pat)

        self.state_manager = StateManager(self, state_file_name)

        if not bypass_initialisation:
            from ado_wrapper.resources.users import AdoUser  # Stop circular imports

            # Verify Token is working (helps with setup for first time users):
            request = self.session.get(f"https://dev.azure.com/{self.ado_org_name}/_apis/projects?api-version=7.1")
            if request.status_code != 200:
                raise AuthenticationError("Failed to authenticate with ADO: Most likely incorrect token or expired token!")

            # =================================================================
            self.assume_project(ado_project_name)

            if ado_email != "" and ado_email is not None:
                try:
                    self.pat_author: AdoUser = AdoUser.get_by_email(self, ado_email)
                except (ValueError, InvalidPermissionsError):
                    if not suppress_warnings:
                        print(
                            f"[ADO_WRAPPER] WARNING: User {ado_email} not found in ADO, nothing critical, but stops releases from being made and PullRequest.set_my_pull_requests_included_teams()"
                        )

            # self.perms = Permission.get_project_perms(self)

    def assume_project(self, project_name: str) -> None:
        """Assumes a different project, meaning that subsequent function calls will use that project.
        As Personal Access Tokens are per organisation, not per project, this will work automatically."""
        from ado_wrapper.resources.projects import Project

        self.ado_project_name = project_name

        self.ado_project_id = Project.get_by_name(self, self.ado_project_name).project_id  # type: ignore[union-attr]
        self.ado_project_pipeline_settings = Project.get_pipeline_settings(self, self.ado_project_name)

    @contextmanager
    def temporary_polling_interval(self, temporary_polling_interval: int) -> Generator[None, None, None]:
        old_polling_interval_in_seconds = self.run_polling_interval_seconds  # Store the old one
        self.run_polling_interval_seconds = temporary_polling_interval  # Set the new one
        yield  # Yield (required)
        self.run_polling_interval_seconds = old_polling_interval_in_seconds  # Restore old functionality

    @contextmanager
    def elevated_privileges(self) -> Generator[None, None, None]:
        self.has_elevate_privileges = True
        yield  # Yield (required)
        self.has_elevate_privileges = False

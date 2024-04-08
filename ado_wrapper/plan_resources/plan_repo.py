from typing import Any

from ado_wrapper.client import AdoClient
from ado_wrapper.resources.repo import Repo

UNKNOWN_UNTIL_APPLY = "Unknown until apply"
BYPASS_CHECK = True

class PlanRepo:
    @staticmethod
    def create(ado_client: AdoClient, _: str, payload: dict[str, Any]) -> Repo:
        name = payload["name"]
        if not BYPASS_CHECK:
            if Repo.get_by_name(ado_client, name):
                raise ValueError(f"Repo {name} already exists")
        return Repo(UNKNOWN_UNTIL_APPLY, name)

from typing import Any, TYPE_CHECKING
# import re
# import requests
# from datetime import datetime

from ado_wrapper.client import AdoClient
# from ado_wrapper.resources.repo import Repo
from ado_wrapper.plan_resources.mapping import get_resource_variables_plans

if TYPE_CHECKING:
    from ado_wrapper.state_managed_abc import StateManagedResource

UNKNOWN_UNTIL_APPLY = "Unknown until apply"

mapping = get_resource_variables_plans()

class PlannedStateManagedResource:

    @staticmethod
    def create(class_: type["StateManagedResource"], ado_client: "AdoClient", url: str, payload: dict[str, Any] | None = None) -> "PlannedStateManagedResource":
        plan_resource = mapping["Plan" + class_.__name__]
        return plan_resource.create(ado_client, url, payload)  # type: ignore[no-any-return]

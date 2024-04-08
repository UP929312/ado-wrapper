from typing import Any, TYPE_CHECKING

from ado_wrapper.client import AdoClient
from ado_wrapper.utils import extract_id

if TYPE_CHECKING:
    from ado_wrapper.state_managed_abc import StateManagedResource

UNKNOWN_UNTIL_APPLY = "Unknown until apply"

class PlannedStateManagedResource:
    @staticmethod
    def create(
        class_: type["StateManagedResource"], ado_client: "AdoClient", url: str, payload: dict[str, Any] | None = None
    ) -> "PlannedStateManagedResource":
        from ado_wrapper.plan_resources.mapping import get_resource_variables_plans

        plan_resource = get_resource_variables_plans()["Plan" + class_.__name__]
        resource_object = plan_resource.create(ado_client, url, payload)
        ado_client.state_manager.add_resource_to_state("Plan" + class_.__name__, extract_id(resource_object), resource_object.to_json())  # type: ignore[arg-type]
        return plan_resource.create(ado_client, url, payload)  # type: ignore[no-any-return]

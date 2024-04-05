from typing import Any


def get_resource_variables_plans() -> dict[str, Any]:  # We do this to avoid circular imports
    from ado_wrapper.plan_resources import (  # type: ignore[attr-defined]  # pylint: disable=possibly-unused-variable
        PlanRepo  # fmt: skip
    )

    return locals()

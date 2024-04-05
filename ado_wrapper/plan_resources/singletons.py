from typing import Any, Callable

import requests

from ado_wrapper.client import AdoClient
from ado_wrapper.plan_resources.mapping import get_resource_variables_plans

mapping = get_resource_variables_plans()

# A decorator that will wrap a Resource.get_by_id method and override the requests.get method temporarily
# to return a custom Fake response


def plannable_resource(func: Callable[[Any, AdoClient], Any]) -> Callable[[Any], Any]:  # fmt: skip
    # requests.get = lambda *_, **__: FakeResponse()
    def inner(cls, ado_client: AdoClient, *args: Any, **kwargs: Any) -> Any:  # type: ignore[no-untyped-def]
        if not ado_client.plan:
            return func(cls, ado_client, *args, **kwargs)
        plan_class = mapping["Plan" + cls.__name__]
        method_type = plan_class.method_types[func.__name__]
        old_requests_method = getattr(requests, method_type)
        setattr(requests, method_type, plan_class.create)
        # rint("Before")
        result = func(cls, ado_client, *args, **kwargs)
        # rint("After")
        setattr(requests, method_type, old_requests_method)
        return result

    return inner  # type: ignore[return-value]

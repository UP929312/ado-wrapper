from typing import Callable, Any
# import re
import requests
# from datetime import datetime

from ado_wrapper.client import AdoClient
from ado_wrapper.resources.repo import Repo

UNKNOWN_UNTIL_APPLY = "Unknown until apply"


class FakeResponse(requests.Response):
    def __init__(self, _json: dict[str, Any], status_code: int) -> None:
        super().__init__()
        self._json = _json
        self.status_code = status_code

    def json(self) -> dict[str, Any]:  # type: ignore[override]
        return self._json


CreateMethod = Callable[[str, dict[str, Any], Any], FakeResponse]


class PlanRepo:
    @staticmethod
    def create(ado_client: AdoClient, name: str, include_readme: bool = True) -> Repo:
        if Repo.get_by_name(ado_client, name):
            raise ValueError(f"Repo {name} already exists")
        repo = Repo(UNKNOWN_UNTIL_APPLY, name)
        # ado_client.state_manager.add_resource_to_state("Repo", name, repo.to_json())  # we need o figure out what we're doing for state?
        return repo

        # Check if the repo with that name already exists in ADO, if so, return a 409?
        # Maybe we should try to update it?
        # Create a cls object, with preset data (from the dumps), and return it
        # Add it to a different state storage.
        # Return the object

        # request = requests.post(url, json=payload if payload is not None else {}, auth=ado_client.auth)  # Create a brand new dict
        # if request.status_code == 401:
        #     raise PermissionError(f"You do not have permission to create this {cls.__name__}!")
        # if request.status_code == 409:
        #     raise ResourceAlreadyExists(f"The {cls.__name__} with that identifier already exist!")
        # resource = cls.from_request_payload(request.json())
        # ado_client.state_manager.add_resource_to_state(cls.__name__, extract_id(resource), resource.to_json())  # type: ignore[arg-type]
        # return resource


# class PlanRepo:
#     method_types = {
#         "create": "post",
#     }

#     @staticmethod
#     def create(url: str, *, json: dict[str, Any], auth: Any) -> FakeResponse:
#         """This is what requests.<x> will get set with, so should have the same signature as the requests.<x> method."""
#         # if re.match()
#         if "/git/repositories?" in url:  # When we're creating the repo
#             return FakeResponse({'id': UnknownUntilApply, 'name': json["name"], 'isDisabled': False,}, 200)
#         elif "/pushes" in url:
#             #member = Member(data["author"]["name"], data["author"]["email"], "UNKNOWN")
#             # return cls(data["commitId"], member, from_ado_date_string(data["author"]["date"]), data["comment"])
#             return FakeResponse({
#                 "commitId": UnknownUntilApply,
#                 "author": {"name": "test", "email": "test", "date": datetime.now().isoformat()},
#                 "comment": "Add README.md",
#             }, 200)
#         return FakeResponse({}, 404)
